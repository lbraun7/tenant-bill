from rest_framework import serializers

from apps.plans.models import Plan
from apps.plans.serializers import PlanSerializer
from apps.subscriptions.models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.none(),
        source="plan",
        write_only=True,
    )

    class Meta:
        model = Subscription
        fields = (
            "id",
            "plan",
            "plan_id",
            "customer_name",
            "customer_email",
            "status",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "external_customer_id",
            "external_subscription_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "plan", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request, "current_tenant"):
            self.fields["plan_id"].queryset = Plan.objects.filter(tenant=request.current_tenant)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start = attrs.get(
            "current_period_start",
            getattr(self.instance, "current_period_start", None),
        )
        end = attrs.get("current_period_end", getattr(self.instance, "current_period_end", None))
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"current_period_end": "Must be after current_period_start."}
            )
        return attrs

    def create(self, validated_data):
        return Subscription.objects.create(
            tenant=self.context["request"].current_tenant,
            **validated_data,
        )
