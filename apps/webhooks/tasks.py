import logging

from celery import shared_task
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.webhooks.handlers import dispatch_webhook
from apps.webhooks.models import WebhookEvent

logger = logging.getLogger(__name__)


def _claim_event(event_id: int) -> bool:
    with transaction.atomic():
        event = WebhookEvent.objects.select_for_update().get(pk=event_id)
        if event.status in {
            WebhookEvent.Status.PROCESSED,
            WebhookEvent.Status.IGNORED,
            WebhookEvent.Status.PROCESSING,
        }:
            return False
        event.status = WebhookEvent.Status.PROCESSING
        event.processing_attempts = F("processing_attempts") + 1
        event.error = ""
        event.save(update_fields=("status", "processing_attempts", "error", "updated_at"))
    return True


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def process_webhook_event(self, event_id: int) -> None:
    if not _claim_event(event_id):
        return

    try:
        with transaction.atomic():
            event = WebhookEvent.objects.select_for_update().get(pk=event_id)
            handled = dispatch_webhook(event.event_type, event.payload)
            event.status = (
                WebhookEvent.Status.PROCESSED if handled else WebhookEvent.Status.IGNORED
            )
            event.processed_at = timezone.now()
            event.error = ""
            event.save(update_fields=("status", "processed_at", "error", "updated_at"))
    except Exception as exc:
        WebhookEvent.objects.filter(pk=event_id).update(
            status=WebhookEvent.Status.FAILED,
            error=str(exc),
            processed_at=None,
            updated_at=timezone.now(),
        )
        logger.exception(
            "stripe_webhook_processing_failed",
            extra={"webhook_event_id": event_id},
        )
        raise

    logger.info(
        "stripe_webhook_processed",
        extra={"webhook_event_id": event_id, "handled": handled},
    )
