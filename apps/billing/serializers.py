from rest_framework import serializers

from apps.billing.models import Invoice, InvoiceLine


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = (
            "id",
            "external_line_id",
            "description",
            "quantity",
            "unit_amount_cents",
            "amount_cents",
            "currency",
            "period_start",
            "period_end",
            "metadata",
        )


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = (
            "id",
            "subscription_id",
            "external_invoice_id",
            "number",
            "status",
            "currency",
            "subtotal_cents",
            "tax_cents",
            "total_cents",
            "amount_paid_cents",
            "amount_due_cents",
            "period_start",
            "period_end",
            "due_at",
            "paid_at",
            "hosted_invoice_url",
            "pdf_url",
            "pdf_generated_at",
            "lines",
            "created_at",
            "updated_at",
        )

    def get_pdf_url(self, invoice):
        if not invoice.pdf:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(invoice.pdf.url) if request else invoice.pdf.url
