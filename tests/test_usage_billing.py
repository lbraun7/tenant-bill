from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.usage.models import UsageEvent
from apps.usage.tasks import sync_usage_event
from tests.factories import (
    PlanFactory,
    SubscriptionFactory,
    TenantFactory,
    TenantMembershipFactory,
    UsageEventFactory,
    UsageMetricFactory,
    UserFactory,
)


@pytest.fixture
def usage_context():
    tenant = TenantFactory()
    user = UserFactory()
    TenantMembershipFactory(tenant=tenant, user=user)
    subscription = SubscriptionFactory(
        plan=PlanFactory(tenant=tenant), external_customer_id="cus_test"
    )
    metric = UsageMetricFactory(tenant=tenant)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, subscription, metric


@pytest.mark.django_db
def test_duplicate_idempotency_key_is_rejected(usage_context):
    client, subscription, metric = usage_context
    payload = {
        "subscription_id": subscription.id,
        "metric_id": metric.id,
        "quantity": 7,
        "idempotency_key": "request-123",
    }

    assert client.post("/api/usage/events/", payload).status_code == 201
    response = client.post("/api/usage/events/", payload)

    assert response.status_code == 400
    assert UsageEvent.objects.filter(idempotency_key="request-123").count() == 1


@pytest.mark.django_db
def test_event_outside_current_billing_period_is_rejected(usage_context):
    client, subscription, metric = usage_context
    response = client.post(
        "/api/usage/events/",
        {
            "subscription_id": subscription.id,
            "metric_id": metric.id,
            "quantity": 1,
            "idempotency_key": "old-event",
            "occurred_at": "2020-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 400
    assert "occurred_at" in response.json()


@pytest.mark.django_db
def test_current_usage_is_aggregated_by_metric_and_period(usage_context):
    client, subscription, metric = usage_context
    UsageEventFactory(subscription=subscription, metric=metric, quantity=4)
    UsageEventFactory(subscription=subscription, metric=metric, quantity=6)

    response = client.get("/api/usage/")

    assert response.status_code == 200
    summary = response.json()[0]
    assert summary["total_quantity"] == 10
    assert summary["metrics"] == [
        {"metric_id": metric.id, "metric_code": metric.code, "quantity": 10}
    ]


@pytest.mark.django_db
def test_usage_event_cannot_be_changed_or_deleted(usage_context):
    _client, subscription, metric = usage_context
    event = UsageEventFactory(subscription=subscription, metric=metric)

    event.quantity = 999
    with pytest.raises(TypeError, match="immutable"):
        event.save()
    with pytest.raises(TypeError, match="immutable"):
        event.delete()


@pytest.mark.django_db
def test_sync_usage_event_uses_isolated_stripe_client(usage_context):
    _client, subscription, metric = usage_context
    event = UsageEventFactory(subscription=subscription, metric=metric, idempotency_key="sync-me")

    with patch("apps.usage.tasks.create_meter_event") as create_meter_event:
        sync_usage_event(event.id)

    create_meter_event.assert_called_once_with(
        event_name=metric.stripe_event_name,
        customer_id="cus_test",
        value=event.quantity,
        identifier=f"usage-{event.tenant_id}-sync-me",
    )
    event.refresh_from_db()
    assert event.sync_status == UsageEvent.SyncStatus.SYNCED
    assert event.synced_at <= timezone.now()
