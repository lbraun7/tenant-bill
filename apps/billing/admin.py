from django.contrib import admin

from apps.billing.models import Invoice, InvoiceLine


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    readonly_fields = ("external_line_id", "created_at")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("external_invoice_id", "tenant", "status", "total_cents", "currency")
    list_filter = ("status", "currency")
    search_fields = ("external_invoice_id", "number", "tenant__name")
    inlines = (InvoiceLineInline,)
