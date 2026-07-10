import pytest
from rest_framework.test import APIClient

from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.usage.models import UsageEvent
from tests.factories import (
    PlanFactory,
    SubscriptionFactory,
    TenantFactory,
    TenantMembershipFactory,
    UsageEventFactory,
    UserFactory,
)


@pytest.fixture
def authenticated_client():
    user = UserFactory()
    tenant = TenantFactory(slug="acme")
    TenantMembershipFactory(user=user, tenant=tenant)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, tenant


@pytest.mark.django_db
def test_create_plan_uses_current_tenant(authenticated_client):
    client, tenant = authenticated_client

    response = client.post(
        "/api/plans/",
        {
            "name": "Growth",
            "price_cents": 9900,
            "currency": "brl",
            "billing_interval": Plan.BillingInterval.MONTH,
            "included_usage_units": 5000,
            "metered_unit_name": "seat",
        },
        content_type="application/json",
    )

    assert response.status_code == 201
    plan = Plan.objects.get(slug="growth")
    assert plan.tenant == tenant
    assert plan.currency == "BRL"


@pytest.mark.django_db
def test_plan_list_is_limited_to_current_tenant(authenticated_client):
    client, tenant = authenticated_client
    own_plan = PlanFactory(tenant=tenant, slug="own-plan")
    PlanFactory(slug="other-plan")

    response = client.get("/api/plans/")

    assert response.status_code == 200
    assert [plan["slug"] for plan in response.json()] == [own_plan.slug]


@pytest.mark.django_db
def test_create_subscription_rejects_plan_from_other_tenant(authenticated_client):
    client, _tenant = authenticated_client
    other_plan = PlanFactory()

    response = client.post(
        "/api/subscriptions/",
        {
            "plan_id": other_plan.id,
            "customer_name": "Jane Customer",
            "customer_email": "jane@example.com",
            "current_period_start": "2026-07-01",
            "current_period_end": "2026-08-01",
        },
        content_type="application/json",
    )

    assert response.status_code == 400
    assert Subscription.objects.count() == 0


@pytest.mark.django_db
def test_create_subscription_uses_current_tenant(authenticated_client):
    client, tenant = authenticated_client
    plan = PlanFactory(tenant=tenant)

    response = client.post(
        "/api/subscriptions/",
        {
            "plan_id": plan.id,
            "customer_name": "Jane Customer",
            "customer_email": "jane@example.com",
            "current_period_start": "2026-07-01",
            "current_period_end": "2026-08-01",
        },
        content_type="application/json",
    )

    assert response.status_code == 201
    subscription = Subscription.objects.get(customer_email="jane@example.com")
    assert subscription.tenant == tenant
    assert subscription.plan == plan


@pytest.mark.django_db
def test_subscription_list_is_limited_to_current_tenant(authenticated_client):
    client, tenant = authenticated_client
    own_subscription = SubscriptionFactory(plan=PlanFactory(tenant=tenant))
    SubscriptionFactory()

    response = client.get("/api/subscriptions/")

    assert response.status_code == 200
    assert [subscription["id"] for subscription in response.json()] == [own_subscription.id]


@pytest.mark.django_db
def test_create_usage_event_rejects_subscription_from_other_tenant(authenticated_client):
    client, _tenant = authenticated_client
    other_subscription = SubscriptionFactory()

    response = client.post(
        "/api/usage-events/",
        {
            "subscription_id": other_subscription.id,
            "quantity": 25,
            "idempotency_key": "usage-1",
        },
        content_type="application/json",
    )

    assert response.status_code == 400
    assert UsageEvent.objects.count() == 0


@pytest.mark.django_db
def test_create_usage_event_uses_current_tenant(authenticated_client):
    client, tenant = authenticated_client
    subscription = SubscriptionFactory(plan=PlanFactory(tenant=tenant))

    response = client.post(
        "/api/usage-events/",
        {
            "subscription_id": subscription.id,
            "quantity": 25,
            "idempotency_key": "usage-1",
            "metadata": {"source": "api"},
        },
        content_type="application/json",
    )

    assert response.status_code == 201
    usage_event = UsageEvent.objects.get(idempotency_key="usage-1")
    assert usage_event.tenant == tenant
    assert usage_event.subscription == subscription


@pytest.mark.django_db
def test_usage_event_list_is_limited_to_current_tenant(authenticated_client):
    client, tenant = authenticated_client
    own_usage_event = UsageEventFactory(
        subscription=SubscriptionFactory(plan=PlanFactory(tenant=tenant))
    )
    UsageEventFactory()

    response = client.get("/api/usage-events/")

    assert response.status_code == 200
    assert [usage_event["id"] for usage_event in response.json()] == [own_usage_event.id]
