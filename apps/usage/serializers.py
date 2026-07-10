from rest_framework import serializers

from apps.subscriptions.models import Subscription
from apps.usage.models import UsageEvent


class UsageEventSerializer(serializers.ModelSerializer):
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.none(),
        source="subscription",
    )

    class Meta:
        model = UsageEvent
        fields = (
            "id",
            "subscription_id",
            "quantity",
            "occurred_at",
            "idempotency_key",
            "metadata",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and hasattr(request, "current_tenant"):
            self.fields["subscription_id"].queryset = Subscription.objects.filter(
                tenant=request.current_tenant
            )

    def create(self, validated_data):
        return UsageEvent.objects.create(
            tenant=self.context["request"].current_tenant,
            **validated_data,
        )
