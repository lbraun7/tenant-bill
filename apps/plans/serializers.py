from rest_framework import serializers

from apps.plans.models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price_cents",
            "currency",
            "billing_interval",
            "included_usage_units",
            "metered_unit_name",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")

    def create(self, validated_data):
        return Plan.objects.create(tenant=self.context["request"].current_tenant, **validated_data)
