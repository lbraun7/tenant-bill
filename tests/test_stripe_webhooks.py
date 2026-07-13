import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from celery.exceptions import Retry
from django.test import override_settings
from rest_framework.test import APIClient

from apps.subscriptions.models import Subscription
from apps.webhooks.models import WebhookEvent
from apps.webhooks.tasks import process_webhook_event
from tests.factories import SubscriptionFactory

WEBHOOK_SECRET = "whsec_test_secret"


def stripe_event(event_id, event_type, event_object):
    return {
        "id": event_id,
        "object": "event",
        "type": event_type,
        "data": {"object": event_object},
    }


def signed_request(event):
    payload = json.dumps(event, separators=(",", ":")).encode()
    timestamp = int(time.time())
    digest = hmac.new(
        WEBHOOK_SECRET.encode(),
        f"{timestamp}.".encode() + payload,
        hashlib.sha256,
    ).hexdigest()
    return payload, f"t={timestamp},v1={digest}"


@pytest.mark.django_db
@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_invalid_stripe_signature_returns_400_and_is_not_persisted():
    client = APIClient()

    response = client.post(
        "/webhooks/stripe/",
        data=b'{"id":"evt_invalid","type":"invoice.paid"}',
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=invalid",
    )

    assert response.status_code == 400
    assert WebhookEvent.objects.count() == 0


@pytest.mark.django_db(transaction=True)
@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_valid_webhook_is_persisted_and_enqueued_after_commit():
    client = APIClient()
    event = stripe_event("evt_valid", "customer.created", {"id": "cus_123"})
    payload, signature = signed_request(event)

    with patch("apps.webhooks.views.process_webhook_event.delay") as delay:
        response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )

    webhook_event = WebhookEvent.objects.get(external_event_id="evt_valid")
    assert response.status_code == 202
    assert response.json() == {"received": True, "duplicate": False}
    assert webhook_event.status == WebhookEvent.Status.RECEIVED
    assert webhook_event.payload == event
    assert webhook_event.enqueued_at is not None
    delay.assert_called_once_with(webhook_event.pk)


@pytest.mark.django_db(transaction=True)
@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_duplicate_webhook_is_acknowledged_without_second_enqueue():
    client = APIClient()
    event = stripe_event("evt_duplicate", "customer.created", {"id": "cus_123"})
    payload, signature = signed_request(event)

    with patch("apps.webhooks.views.process_webhook_event.delay") as delay:
        first_response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )
        second_response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )

    assert first_response.status_code == 202
    assert second_response.status_code == 200
    assert second_response.json() == {"received": True, "duplicate": True}
    assert WebhookEvent.objects.filter(external_event_id="evt_duplicate").count() == 1
    delay.assert_called_once()


@pytest.mark.django_db(transaction=True)
@override_settings(STRIPE_WEBHOOK_SECRET=WEBHOOK_SECRET)
def test_duplicate_delivery_retries_enqueue_after_broker_failure():
    client = APIClient()
    event = stripe_event("evt_broker_retry", "customer.created", {"id": "cus_123"})
    payload, signature = signed_request(event)

    with (
        patch(
            "apps.webhooks.views.process_webhook_event.delay",
            side_effect=RuntimeError("broker unavailable"),
        ),
        pytest.raises(RuntimeError, match="broker unavailable"),
    ):
        client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )

    webhook_event = WebhookEvent.objects.get(external_event_id="evt_broker_retry")
    assert webhook_event.status == WebhookEvent.Status.RECEIVED
    assert webhook_event.enqueued_at is None

    with patch("apps.webhooks.views.process_webhook_event.delay") as delay:
        response = client.post(
            "/webhooks/stripe/",
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=signature,
        )

    webhook_event.refresh_from_db()
    assert response.status_code == 200
    assert response.json() == {"received": True, "duplicate": True}
    assert webhook_event.enqueued_at is not None
    delay.assert_called_once_with(webhook_event.pk)


@pytest.mark.django_db
def test_checkout_completed_links_the_local_subscription_only_once():
    subscription = SubscriptionFactory(
        status=Subscription.Status.TRIALING,
        external_customer_id="",
        external_subscription_id="",
    )
    event = WebhookEvent.objects.create(
        provider="stripe",
        external_event_id="evt_checkout",
        event_type="checkout.session.completed",
        payload=stripe_event(
            "evt_checkout",
            "checkout.session.completed",
            {
                "id": "cs_123",
                "customer": "cus_123",
                "subscription": "sub_123",
                "metadata": {"subscription_id": str(subscription.pk)},
            },
        ),
    )

    process_webhook_event.run(event.pk)
    process_webhook_event.run(event.pk)

    subscription.refresh_from_db()
    event.refresh_from_db()
    assert subscription.external_customer_id == "cus_123"
    assert subscription.external_subscription_id == "sub_123"
    assert subscription.status == Subscription.Status.ACTIVE
    assert event.status == WebhookEvent.Status.PROCESSED
    assert event.processing_attempts == 1
    assert event.processed_at is not None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("event_type", "initial_status", "expected_status"),
    [
        ("invoice.paid", Subscription.Status.PAST_DUE, Subscription.Status.ACTIVE),
        ("invoice.payment_failed", Subscription.Status.ACTIVE, Subscription.Status.PAST_DUE),
    ],
)
def test_invoice_events_update_the_local_subscription_status(
    event_type,
    initial_status,
    expected_status,
):
    subscription = SubscriptionFactory(
        external_subscription_id="sub_invoice",
        status=initial_status,
    )
    event = WebhookEvent.objects.create(
        provider="stripe",
        external_event_id=f"evt_{event_type}",
        event_type=event_type,
        payload=stripe_event(
            f"evt_{event_type}",
            event_type,
            {"id": "in_123", "subscription": subscription.external_subscription_id},
        ),
    )

    process_webhook_event.run(event.pk)

    subscription.refresh_from_db()
    assert subscription.status == expected_status


@pytest.mark.django_db
def test_subscription_updated_synchronizes_status_period_and_cancel_flag():
    subscription = SubscriptionFactory(
        external_subscription_id="sub_updated",
        status=Subscription.Status.ACTIVE,
    )
    period_start = datetime(2026, 8, 1, tzinfo=UTC)
    period_end = datetime(2026, 9, 1, tzinfo=UTC)
    event = WebhookEvent.objects.create(
        provider="stripe",
        external_event_id="evt_subscription_updated",
        event_type="customer.subscription.updated",
        payload=stripe_event(
            "evt_subscription_updated",
            "customer.subscription.updated",
            {
                "id": subscription.external_subscription_id,
                "customer": "cus_updated",
                "status": "past_due",
                "cancel_at_period_end": True,
                "current_period_start": int(period_start.timestamp()),
                "current_period_end": int(period_end.timestamp()),
            },
        ),
    )

    process_webhook_event.run(event.pk)

    subscription.refresh_from_db()
    assert subscription.status == Subscription.Status.PAST_DUE
    assert subscription.external_customer_id == "cus_updated"
    assert subscription.cancel_at_period_end is True
    assert subscription.current_period_start == period_start.date()
    assert subscription.current_period_end == period_end.date()


@pytest.mark.django_db
def test_subscription_deleted_marks_the_local_subscription_as_canceled():
    subscription = SubscriptionFactory(
        external_subscription_id="sub_deleted",
        status=Subscription.Status.ACTIVE,
        cancel_at_period_end=True,
    )
    event = WebhookEvent.objects.create(
        provider="stripe",
        external_event_id="evt_subscription_deleted",
        event_type="customer.subscription.deleted",
        payload=stripe_event(
            "evt_subscription_deleted",
            "customer.subscription.deleted",
            {"id": subscription.external_subscription_id},
        ),
    )

    process_webhook_event.run(event.pk)

    subscription.refresh_from_db()
    assert subscription.status == Subscription.Status.CANCELED
    assert subscription.cancel_at_period_end is False


@pytest.mark.django_db
def test_unknown_event_is_recorded_as_ignored():
    event = WebhookEvent.objects.create(
        provider="stripe",
        external_event_id="evt_unknown",
        event_type="customer.created",
        payload=stripe_event("evt_unknown", "customer.created", {"id": "cus_123"}),
    )

    process_webhook_event.run(event.pk)

    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.IGNORED
    assert event.processing_attempts == 1
    assert event.processed_at is not None


@pytest.mark.django_db
def test_processing_failure_is_persisted_and_schedules_a_retry():
    event = WebhookEvent.objects.create(
        provider="stripe",
        external_event_id="evt_retry",
        event_type="invoice.paid",
        payload=stripe_event(
            "evt_retry",
            "invoice.paid",
            {"id": "in_missing", "subscription": "sub_missing"},
        ),
    )

    with pytest.raises(Retry, match="sub_missing"):
        process_webhook_event.apply(args=(event.pk,), throw=True)

    event.refresh_from_db()
    assert event.status == WebhookEvent.Status.FAILED
    assert event.processing_attempts == 1
    assert "sub_missing" in event.error
    assert event.processed_at is None
