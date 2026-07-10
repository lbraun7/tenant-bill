import pytest
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, TenantMembership


@pytest.mark.django_db
def test_register_creates_user_tenant_owner_membership(client):
    response = client.post(
        "/api/auth/register/",
        {
            "email": "owner@example.com",
            "password": "strong-password",
            "name": "Owner",
            "tenant_name": "Acme Inc",
            "tenant_slug": "acme",
        },
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "owner@example.com"
    assert body["tenant"]["slug"] == "acme"
    assert "access" in body["tokens"]
    assert "refresh" in body["tokens"]

    user = get_user_model().objects.get(email="owner@example.com")
    tenant = Tenant.objects.get(slug="acme")
    assert TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        role=TenantMembership.Role.OWNER,
        is_active=True,
    ).exists()
