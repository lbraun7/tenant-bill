from django.db import models

from apps.plans.models import Plan
from apps.tenants.models import Tenant


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIALING = "trialing", "Trialing"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        CANCELED = "canceled", "Canceled"

    tenant = models.ForeignKey(Tenant, related_name="subscriptions", on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, related_name="subscriptions", on_delete=models.PROTECT)
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    cancel_at_period_end = models.BooleanField(default=False)
    external_customer_id = models.CharField(max_length=255, blank=True)
    external_subscription_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["customer_name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(current_period_end__gt=models.F("current_period_start")),
                name="subscription_period_end_after_start",
            ),
            models.UniqueConstraint(
                fields=("external_subscription_id",),
                condition=~models.Q(external_subscription_id=""),
                name="unique_non_empty_external_subscription_id",
            ),
        ]

    def __str__(self):
        return f"{self.customer_email} - {self.plan}"
