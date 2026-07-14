from datetime import UTC, datetime
from typing import Any

from django.db import transaction

from apps.billing.models import Invoice, InvoiceLine
from apps.subscriptions.models import Subscription
from apps.webhooks.errors import WebhookProcessingError


def _timestamp(value: Any):
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OSError) as exc:
        raise WebhookProcessingError(f"Invalid Stripe invoice timestamp: {value!r}.") from exc


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError) as exc:
        raise WebhookProcessingError(f"Invalid Stripe invoice amount: {value!r}.") from exc


def sync_invoice(subscription: Subscription, data: dict[str, Any], *, status: str) -> Invoice:
    external_id = str(data.get("id") or "")
    if not external_id:
        raise WebhookProcessingError("Stripe invoice is missing its id.")

    status_mapping = {
        "draft": Invoice.Status.DRAFT,
        "open": Invoice.Status.OPEN,
        "paid": Invoice.Status.PAID,
        "uncollectible": Invoice.Status.UNCOLLECTIBLE,
        "void": Invoice.Status.VOID,
        "payment_failed": Invoice.Status.OPEN,
    }
    local_status = status_mapping.get(status)
    if local_status is None:
        raise WebhookProcessingError(f"Unsupported Stripe invoice status: {status!r}.")

    currency = str(data.get("currency") or subscription.plan.currency).upper()
    status_transitions = data.get("status_transitions") or {}
    with transaction.atomic():
        invoice, _ = Invoice.objects.update_or_create(
            external_invoice_id=external_id,
            defaults={
                "tenant": subscription.tenant,
                "subscription": subscription,
                "number": str(data.get("number") or ""),
                "status": local_status,
                "currency": currency,
                "subtotal_cents": _non_negative_int(data.get("subtotal")),
                "tax_cents": _non_negative_int(data.get("tax")),
                "total_cents": _non_negative_int(data.get("total")),
                "amount_paid_cents": _non_negative_int(data.get("amount_paid")),
                "amount_due_cents": _non_negative_int(data.get("amount_due")),
                "period_start": _timestamp(data.get("period_start")),
                "period_end": _timestamp(data.get("period_end")),
                "due_at": _timestamp(data.get("due_date")),
                "paid_at": _timestamp(status_transitions.get("paid_at")),
                "hosted_invoice_url": str(data.get("hosted_invoice_url") or ""),
            },
        )

        stripe_lines = (data.get("lines") or {}).get("data") or []
        for index, line in enumerate(stripe_lines):
            line_id = str(line.get("id") or f"{external_id}:line:{index}")
            quantity = _non_negative_int(line.get("quantity") or 1)
            amount = _non_negative_int(line.get("amount"))
            period = line.get("period") or {}
            InvoiceLine.objects.update_or_create(
                invoice=invoice,
                external_line_id=line_id,
                defaults={
                    "description": str(line.get("description") or ""),
                    "quantity": quantity,
                    "unit_amount_cents": amount // quantity if quantity else amount,
                    "amount_cents": amount,
                    "currency": str(line.get("currency") or currency).upper(),
                    "period_start": _timestamp(period.get("start")),
                    "period_end": _timestamp(period.get("end")),
                    "metadata": line.get("metadata") or {},
                },
            )
    return invoice
