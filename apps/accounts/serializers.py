from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.tenants.models import Tenant, TenantMembership


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    tenant_name = serializers.CharField(max_length=255)
    tenant_slug = serializers.SlugField(max_length=255, required=False, allow_blank=True)

    def validate_email(self, value):
        User = get_user_model()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    @transaction.atomic
    def create(self, validated_data):
        User = get_user_model()
        email = validated_data["email"]
        name = validated_data.get("name", "").strip()
        tenant_slug = validated_data.get("tenant_slug", "").strip()

        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            first_name=name,
        )
        tenant = Tenant.objects.create(
            name=validated_data["tenant_name"],
            slug=tenant_slug,
        )
        TenantMembership.objects.create(
            tenant=tenant,
            user=user,
            role=TenantMembership.Role.OWNER,
        )
        return {"user": user, "tenant": tenant}

    def to_representation(self, instance):
        user = instance["user"]
        tenant = instance["tenant"]
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.first_name,
            },
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
            },
        }
