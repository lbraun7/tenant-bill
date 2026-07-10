from django.contrib import admin

from apps.usage.models import UsageEvent


@admin.register(UsageEvent)
class UsageEventAdmin(admin.ModelAdmin):
    list_display = ("subscription", "tenant", "quantity", "occurred_at", "idempotency_key")
    search_fields = ("subscription__customer_email", "tenant__name", "idempotency_key")
