from unittest.mock import patch

from django.test import override_settings

from apps.integrations.stripe.client import create_meter_event


@override_settings(STRIPE_SECRET_KEY="sk_test_configured")
def test_meter_event_uses_configured_stripe_api_key():
    with patch(
        "apps.integrations.stripe.client.stripe.billing.MeterEvent.create"
    ) as meter_event_create:
        create_meter_event(
            event_name="api_requests",
            customer_id="cus_test",
            value=25,
            identifier="usage-1-request-123",
        )

    meter_event_create.assert_called_once_with(
        event_name="api_requests",
        identifier="usage-1-request-123",
        payload={"stripe_customer_id": "cus_test", "value": "25"},
        api_key="sk_test_configured",
    )
