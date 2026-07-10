from django.contrib import admin

from apps.plans.models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "price_cents", "currency", "billing_interval", "is_active")
    list_filter = ("billing_interval", "currency", "is_active")
    search_fields = ("name", "slug", "tenant__name")
