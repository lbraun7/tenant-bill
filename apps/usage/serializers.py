from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from apps.subscriptions.models import Subscription
from apps.usage.models import UsageEvent, UsageMetric


class UsageMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageMetric
        fields = ("id", "name", "code", "unit_name", "stripe_event_name", "is_active")
        read_only_fields = ("id",)


class UsageEventSerializer(serializers.ModelSerializer):
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.none(),
        source="subscription",
    )
    metric_id = serializers.PrimaryKeyRelatedField(
        queryset=UsageMetric.objects.none(), source="metric", required=False
    )

    class Meta:
        model = UsageEvent
        fields = (
            "id",
            "subscription_id",
            "metric_id",
            "quantity",
            "occurred_at",
            "idempotency_key",
            "metadata",
            "created_at",
            "sync_status",
            "synced_at",
            "sync_error",
        )
        read_only_fields = ("id", "created_at", "sync_status", "synced_at", "sync_error")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request, "current_tenant"):
            self.fields["subscription_id"].queryset = Subscription.objects.filter(
                tenant=request.current_tenant
            )
            self.fields["metric_id"].queryset = UsageMetric.objects.filter(
                tenant=request.current_tenant, is_active=True
            )

    def validate(self, attrs):
        subscription = attrs["subscription"]
        occurred_at = attrs.get("occurred_at") or timezone.now()
        in_current_period = (
            subscription.current_period_start
            <= occurred_at.date()
            < subscription.current_period_end
        )
        if not in_current_period:
            raise serializers.ValidationError(
                {"occurred_at": "Usage must fall inside the subscription billing period."}
            )
        if not attrs.get("idempotency_key"):
            raise serializers.ValidationError({"idempotency_key": "This field is required."})
        metric = attrs.get("metric")
        if metric is None:
            metric, _ = UsageMetric.objects.get_or_create(
                tenant=subscription.tenant,
                code=subscription.plan.metered_unit_name,
                defaults={
                    "name": subscription.plan.metered_unit_name.replace("_", " ").title(),
                    "unit_name": subscription.plan.metered_unit_name,
                },
            )
            attrs["metric"] = metric
        return attrs

    def create(self, validated_data):
        tenant = self.context["request"].current_tenant
        if UsageEvent.objects.filter(
            tenant=tenant, idempotency_key=validated_data["idempotency_key"]
        ).exists():
            raise serializers.ValidationError({"idempotency_key": "Duplicate usage event."})
        try:
            with transaction.atomic():
                event = UsageEvent.objects.create(tenant=tenant, **validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"idempotency_key": "Duplicate usage event."}
            ) from exc
        from apps.usage.tasks import sync_usage_event

        transaction.on_commit(lambda: sync_usage_event.delay(event.pk), robust=True)
        return event


class CurrentUsageMetricSerializer(serializers.Serializer):
    metric_id = serializers.IntegerField(allow_null=True)
    metric_code = serializers.CharField(allow_null=True)
    quantity = serializers.IntegerField()


class CurrentUsageSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    included_units = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    metrics = CurrentUsageMetricSerializer(many=True)
