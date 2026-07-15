from django.db import models
from django.utils import timezone

from apps.subscriptions.models import Subscription
from apps.tenants.models import Tenant


class UsageMetric(models.Model):
    tenant = models.ForeignKey(Tenant, related_name="usage_metrics", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    code = models.SlugField(max_length=120)
    unit_name = models.CharField(max_length=80)
    stripe_event_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name", "id")
        constraints = [
            models.UniqueConstraint(fields=("tenant", "code"), name="unique_usage_metric_code")
        ]

    def __str__(self):
        return f"{self.name} ({self.unit_name})"


class UsageEvent(models.Model):
    class SyncStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SYNCED = "synced", "Synced"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey(Tenant, related_name="usage_events", on_delete=models.CASCADE)
    subscription = models.ForeignKey(
        Subscription,
        related_name="usage_events",
        on_delete=models.CASCADE,
    )
    metric = models.ForeignKey(
        UsageMetric,
        related_name="events",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField()
    occurred_at = models.DateTimeField(default=timezone.now)
    idempotency_key = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(
        max_length=20, choices=SyncStatus.choices, default=SyncStatus.PENDING
    )
    synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.TextField(blank=True)

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

    def save(self, *args, **kwargs):
        if self.pk:
            raise TypeError("Usage events are immutable ledger entries.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError("Usage events are immutable ledger entries.")
