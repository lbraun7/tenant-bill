from django.contrib import admin

from apps.usage.models import UsageEvent, UsageMetric


@admin.register(UsageMetric)
class UsageMetricAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "tenant", "unit_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "tenant__name", "stripe_event_name")


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ("subscription", "metric", "tenant", "quantity", "occurred_at", "sync_status")
    list_filter = ("sync_status", "metric")
    search_fields = ("subscription__customer_email", "tenant__name", "idempotency_key")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
