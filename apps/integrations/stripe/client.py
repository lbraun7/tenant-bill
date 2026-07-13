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
