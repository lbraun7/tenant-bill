from django.contrib import admin

from apps.subscriptions.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("customer_email", "tenant", "plan", "status", "current_period_end")
    list_filter = ("status", "cancel_at_period_end")
    search_fields = ("customer_email", "customer_name", "tenant__name", "plan__name")
