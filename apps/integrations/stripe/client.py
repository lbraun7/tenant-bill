import json
from typing import Any

import stripe
from django.conf import settings

from apps.integrations.stripe.errors import InvalidWebhookError


def verify_webhook_event(payload: bytes, signature: str) -> dict[str, Any]:
    """Authenticate a Stripe webhook and return a JSON-compatible event."""
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise InvalidWebhookError("Invalid Stripe webhook signature or payload.") from exc

    return json.loads(json.dumps(event))


def create_meter_event(*, event_name: str, customer_id: str, value: int, identifier: str):
    """Send usage through the Stripe boundary so callers remain SDK-agnostic."""
    try:
        return stripe.billing.MeterEvent.create(
            event_name=event_name,
            identifier=identifier,
            payload={"stripe_customer_id": customer_id, "value": str(value)},
        )
    except stripe.StripeError as exc:
        raise RuntimeError("Stripe rejected the meter event.") from exc
