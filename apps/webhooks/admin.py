from django.contrib import admin

from apps.webhooks.models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "external_event_id",
        "event_type",
        "provider",
        "status",
        "processing_attempts",
        "created_at",
    )
    list_filter = ("provider", "status", "event_type")
    search_fields = ("external_event_id", "event_type", "error")
    readonly_fields = (
        "provider",
        "external_event_id",
        "event_type",
        "payload",
        "status",
        "processing_attempts",
        "enqueued_at",
        "processed_at",
        "error",
        "created_at",
        "updated_at",
    )
