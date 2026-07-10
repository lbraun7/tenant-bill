import pytest
from rest_framework.test import APIClient

from tests.factories import TenantFactory, TenantMembershipFactory, UserFactory


@pytest.mark.django_db
def test_user_lists_only_own_tenants():
    user = UserFactory()
    own_tenant = TenantFactory(slug="own-tenant")
    other_tenant = TenantFactory(slug="other-tenant")
    TenantMembershipFactory(user=user, tenant=own_tenant)
    TenantMembershipFactory(tenant=other_tenant)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/tenants/")

    assert response.status_code == 200
    assert [tenant["slug"] for tenant in response.json()] == ["own-tenant"]


@pytest.mark.django_db
def test_user_cannot_retrieve_tenant_from_another_membership():
    user = UserFactory()
    own_tenant = TenantFactory(slug="own-tenant")
    other_tenant = TenantFactory(slug="other-tenant")
    TenantMembershipFactory(user=user, tenant=own_tenant)
    TenantMembershipFactory(tenant=other_tenant)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/tenants/other-tenant/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_current_tenant_header_must_belong_to_authenticated_user():
    user = UserFactory()
    other_tenant = TenantFactory(slug="other-tenant")
    TenantMembershipFactory(tenant=other_tenant)

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/tenants/me/", HTTP_X_TENANT_SLUG="other-tenant")

    assert response.status_code == 403
