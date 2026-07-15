from celery import shared_task
from django.utils import timezone

from apps.integrations.stripe.client import create_meter_event
from apps.usage.models import UsageEvent


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_usage_event(self, event_id: int) -> None:
    event = UsageEvent.objects.select_related("metric", "subscription").get(pk=event_id)
    if event.sync_status == UsageEvent.SyncStatus.SYNCED:
        return
    try:
        if not event.metric or not event.metric.stripe_event_name:
            raise ValueError("Usage metric has no Stripe event name.")
        if not event.subscription.external_customer_id:
            raise ValueError("Subscription has no Stripe customer id.")
        create_meter_event(
            event_name=event.metric.stripe_event_name,
            customer_id=event.subscription.external_customer_id,
            value=event.quantity,
            identifier=f"usage-{event.tenant_id}-{event.idempotency_key}",
        )
    except Exception as exc:
        UsageEvent.objects.filter(pk=event.pk).update(
            sync_status=UsageEvent.SyncStatus.FAILED, sync_error=str(exc)
        )
        raise
    UsageEvent.objects.filter(pk=event.pk).update(
        sync_status=UsageEvent.SyncStatus.SYNCED,
        synced_at=timezone.now(),
        sync_error="",
    )
