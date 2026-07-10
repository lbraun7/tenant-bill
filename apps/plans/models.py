from django.db import models
from django.utils.text import slugify

from apps.tenants.models import Tenant


class Plan(models.Model):
    class BillingInterval(models.TextChoices):
        MONTH = "month", "Month"
        YEAR = "year", "Year"

    tenant = models.ForeignKey(Tenant, related_name="plans", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTH,
    )
    included_usage_units = models.PositiveIntegerField(default=0)
    metered_unit_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "slug"], name="unique_plan_slug_per_tenant")
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.currency = self.currency.upper()
        super().save(*args, **kwargs)
