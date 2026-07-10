from rest_framework.permissions import BasePermission

from apps.tenants.selectors import get_current_tenant


class HasCurrentTenant(BasePermission):
    message = "Authenticated user does not belong to the requested tenant."

    def has_permission(self, request, view):
        request.current_tenant = get_current_tenant(request)
        return request.current_tenant is not None
