from django.db import models
from django.utils import timezone

from apps.subscriptions.models import Subscription
from apps.tenants.models import Tenant


class UsageEvent(models.Model):
    tenant = models.ForeignKey(Tenant, related_name="usage_events", on_delete=models.CASCADE)
    subscription = models.ForeignKey(
        Subscription,
        related_name="usage_events",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField()
    occurred_at = models.DateTimeField(default=timezone.now)
    idempotency_key = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="unique_usage_idempotency_key_per_tenant",
            )
        ]

    def __str__(self):
        return f"{self.quantity} units for {self.subscription_id}"
