from django.db import models

from apps.subscriptions.models import Subscription
from apps.tenants.models import Tenant


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        PAID = "paid", "Paid"
        UNCOLLECTIBLE = "uncollectible", "Uncollectible"
        VOID = "void", "Void"

    tenant = models.ForeignKey(Tenant, related_name="invoices", on_delete=models.CASCADE)
    subscription = models.ForeignKey(
        Subscription,
        related_name="invoices",
        on_delete=models.PROTECT,
    )
    external_invoice_id = models.CharField(max_length=255, unique=True)
    number = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    currency = models.CharField(max_length=3)
    subtotal_cents = models.PositiveIntegerField(default=0)
    tax_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)
    amount_paid_cents = models.PositiveIntegerField(default=0)
    amount_due_cents = models.PositiveIntegerField(default=0)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    hosted_invoice_url = models.URLField(blank=True)
    pdf = models.FileField(upload_to="invoices/%Y/%m/", blank=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.number or self.external_invoice_id


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="lines", on_delete=models.CASCADE)
    external_line_id = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_amount_cents = models.PositiveIntegerField(default=0)
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=("invoice", "external_line_id"),
                name="unique_external_line_per_invoice",
            )
        ]

    def __str__(self):
        return self.description or self.external_line_id
