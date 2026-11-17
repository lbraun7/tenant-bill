import json
import logging

import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.billing.models import Invoice
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.tenants.models import Tenant, TenantMembership
from apps.usage.models import UsageEvent, UsageMetric
from config.logging import JsonFormatter


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")

    tenant = Tenant.objects.get(slug="acme-demo")
    assert TenantMembership.objects.filter(tenant=tenant, role="owner").count() == 1
    assert Plan.objects.filter(tenant=tenant, slug="growth").count() == 1
    subscription = Subscription.objects.get(external_subscription_id="sub_demo_growth")
    assert UsageMetric.objects.filter(tenant=tenant, code="api-requests").count() == 1
    usage_event = UsageEvent.objects.get(
        tenant=tenant,
        idempotency_key=f"demo-usage-{subscription.current_period_start.isoformat()}",
    )
    assert usage_event.quantity == 1250
    assert (
        subscription.current_period_start
        <= usage_event.occurred_at.date()
        < subscription.current_period_end
    )
    assert Invoice.objects.filter(external_invoice_id="in_demo_001").count() == 1


def test_json_log_formatter_preserves_structured_context():
    record = logging.LogRecord(
        "apps.webhooks.tasks",
        logging.INFO,
        __file__,
        1,
        "stripe_webhook_processed",
        (),
        None,
    )
    record.webhook_event_id = 42

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "stripe_webhook_processed"
    assert payload["level"] == "INFO"
    assert payload["webhook_event_id"] == 42


def test_openapi_documentation_endpoints_are_available(client):
    assert client.get(reverse("schema")).status_code == 200
    assert client.get(reverse("swagger-ui")).status_code == 200
    assert client.get(reverse("redoc")).status_code == 200
