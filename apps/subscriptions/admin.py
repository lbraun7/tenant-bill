from django.contrib import admin

from apps.subscriptions.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "customer_email",
        "tenant",
        "plan",
        "status",
        "external_subscription_id",
        "current_period_end",
    )
    list_filter = ("status", "cancel_at_period_end")
    search_fields = (
        "customer_email",
        "customer_name",
        "tenant__name",
        "tenant__slug",
        "plan__name",
        "external_customer_id",
        "external_subscription_id",
    )
    autocomplete_fields = ("tenant", "plan")
    date_hierarchy = "created_at"
