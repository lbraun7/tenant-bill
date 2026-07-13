from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from apps.subscriptions.models import Subscription
from apps.webhooks.errors import WebhookProcessingError

Handler = Callable[[dict[str, Any]], None]


def _event_object(payload: dict[str, Any]) -> dict[str, Any]:
    event_object = payload.get("data", {}).get("object", {})
    if not isinstance(event_object, dict):
        raise WebhookProcessingError("Webhook data.object must be an object.")
    return event_object


def _reference_id(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("id", ""))
    return str(value or "")


def _subscription_by_external_id(external_id: str) -> Subscription:
    if not external_id:
        raise WebhookProcessingError("Webhook does not reference a Stripe subscription.")
    try:
        return Subscription.objects.get(external_subscription_id=external_id)
    except Subscription.DoesNotExist as exc:
        raise WebhookProcessingError(
            f"Local subscription for Stripe subscription {external_id!r} was not found."
        ) from exc
    except Subscription.MultipleObjectsReturned as exc:
        raise WebhookProcessingError(
            f"Stripe subscription {external_id!r} maps to multiple local subscriptions."
        ) from exc


def _invoice_subscription_id(invoice: dict[str, Any]) -> str:
    direct_reference = _reference_id(invoice.get("subscription"))
    if direct_reference:
        return direct_reference
    return _reference_id(
        invoice.get("parent", {}).get("subscription_details", {}).get("subscription")
    )


def _stripe_status(status: str) -> str:
    mapping = {
        "trialing": Subscription.Status.TRIALING,
        "active": Subscription.Status.ACTIVE,
        "past_due": Subscription.Status.PAST_DUE,
        "canceled": Subscription.Status.CANCELED,
        "incomplete": Subscription.Status.PAST_DUE,
        "incomplete_expired": Subscription.Status.CANCELED,
        "unpaid": Subscription.Status.PAST_DUE,
        "paused": Subscription.Status.PAST_DUE,
    }
    try:
        return mapping[status]
    except KeyError as exc:
        raise WebhookProcessingError(
            f"Unsupported Stripe subscription status: {status!r}."
        ) from exc


def _timestamp_date(value: Any):
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=UTC).date()
    except (TypeError, ValueError, OSError) as exc:
        raise WebhookProcessingError(f"Invalid Stripe period timestamp: {value!r}.") from exc


def handle_checkout_session_completed(payload: dict[str, Any]) -> None:
    session = _event_object(payload)
    metadata = session.get("metadata") or {}
    local_subscription_id = metadata.get("subscription_id") or session.get("client_reference_id")
    if not local_subscription_id:
        raise WebhookProcessingError("Checkout session is missing the local subscription id.")

    try:
        subscription = Subscription.objects.get(pk=local_subscription_id)
    except (Subscription.DoesNotExist, ValueError, TypeError) as exc:
        raise WebhookProcessingError(
            f"Local subscription {local_subscription_id!r} was not found."
        ) from exc

    external_subscription_id = _reference_id(session.get("subscription"))
    if not external_subscription_id:
        raise WebhookProcessingError("Checkout session is missing the Stripe subscription id.")

    subscription.external_customer_id = _reference_id(session.get("customer"))
    subscription.external_subscription_id = external_subscription_id
    subscription.status = Subscription.Status.ACTIVE
    subscription.save(
        update_fields=(
            "external_customer_id",
            "external_subscription_id",
            "status",
            "updated_at",
        )
    )


def handle_invoice_paid(payload: dict[str, Any]) -> None:
    invoice = _event_object(payload)
    subscription = _subscription_by_external_id(_invoice_subscription_id(invoice))
    subscription.status = Subscription.Status.ACTIVE
    subscription.save(update_fields=("status", "updated_at"))


def handle_invoice_payment_failed(payload: dict[str, Any]) -> None:
    invoice = _event_object(payload)
    subscription = _subscription_by_external_id(_invoice_subscription_id(invoice))
    subscription.status = Subscription.Status.PAST_DUE
    subscription.save(update_fields=("status", "updated_at"))


def handle_subscription_updated(payload: dict[str, Any]) -> None:
    stripe_subscription = _event_object(payload)
    subscription = _subscription_by_external_id(_reference_id(stripe_subscription.get("id")))
    subscription.status = _stripe_status(stripe_subscription.get("status", ""))
    subscription.cancel_at_period_end = bool(stripe_subscription.get("cancel_at_period_end", False))

    customer_id = _reference_id(stripe_subscription.get("customer"))
    if customer_id:
        subscription.external_customer_id = customer_id

    period_start = _timestamp_date(stripe_subscription.get("current_period_start"))
    period_end = _timestamp_date(stripe_subscription.get("current_period_end"))
    if period_start is not None and period_end is not None:
        if period_end <= period_start:
            raise WebhookProcessingError("Stripe subscription period end must be after its start.")
        subscription.current_period_start = period_start
        subscription.current_period_end = period_end

    subscription.save()


def handle_subscription_deleted(payload: dict[str, Any]) -> None:
    stripe_subscription = _event_object(payload)
    subscription = _subscription_by_external_id(_reference_id(stripe_subscription.get("id")))
    subscription.status = Subscription.Status.CANCELED
    subscription.cancel_at_period_end = False
    subscription.save(update_fields=("status", "cancel_at_period_end", "updated_at"))


HANDLERS: dict[str, Handler] = {
    "checkout.session.completed": handle_checkout_session_completed,
    "invoice.paid": handle_invoice_paid,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
}


def dispatch_webhook(event_type: str, payload: dict[str, Any]) -> bool:
    handler = HANDLERS.get(event_type)
    if handler is None:
        return False
    handler(payload)
    return True
