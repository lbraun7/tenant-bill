from apps.tenants.models import Tenant, TenantMembership


def get_current_tenant(request) -> Tenant | None:
    if not request.user.is_authenticated:
        return None

    slug = request.headers.get("X-Tenant-Slug")
    memberships = TenantMembership.objects.select_related("tenant").filter(
        user=request.user,
        is_active=True,
    )
    if slug:
        membership = memberships.filter(tenant__slug=slug).first()
        return membership.tenant if membership else None

    membership = memberships.order_by("created_at").first()
    return membership.tenant if membership else None
