from functools import partial

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.stripe.client import verify_webhook_event
from apps.integrations.stripe.errors import InvalidWebhookError
from apps.webhooks.models import WebhookEvent
from apps.webhooks.tasks import process_webhook_event


def enqueue_webhook_event(event_id: int) -> None:
    process_webhook_event.delay(event_id)
    WebhookEvent.objects.filter(
        pk=event_id,
        status=WebhookEvent.Status.RECEIVED,
        enqueued_at__isnull=True,
    ).update(enqueued_at=timezone.now(), updated_at=timezone.now())


class StripeWebhookView(APIView):
    authentication_classes = ()
    permission_classes = ()

    @extend_schema(exclude=True)
    def post(self, request):
        try:
            payload = verify_webhook_event(
                payload=request.body,
                signature=request.headers.get("Stripe-Signature", ""),
            )
        except InvalidWebhookError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        external_event_id = payload.get("id")
        event_type = payload.get("type")
        if not external_event_id or not event_type:
            return Response(
                {"detail": "Stripe event must include id and type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            webhook_event, created = WebhookEvent.objects.get_or_create(
                external_event_id=external_event_id,
                defaults={
                    "provider": "stripe",
                    "event_type": event_type,
                    "payload": payload,
                },
            )
            should_enqueue = created or (
                webhook_event.status == WebhookEvent.Status.RECEIVED
                and webhook_event.enqueued_at is None
            )
            if should_enqueue:
                transaction.on_commit(partial(enqueue_webhook_event, webhook_event.pk))

        response_status = status.HTTP_202_ACCEPTED if created else status.HTTP_200_OK
        return Response({"received": True, "duplicate": not created}, status=response_status)
