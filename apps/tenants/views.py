from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tenants.models import Tenant
from apps.tenants.permissions import HasCurrentTenant
from apps.tenants.serializers import TenantSerializer


class TenantViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Tenant.objects.none()
    serializer_class = TenantSerializer
    permission_classes = (IsAuthenticated, HasCurrentTenant)
    lookup_field = "slug"
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return Tenant.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
        ).distinct()

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        tenant = request.current_tenant
        if request.method == "PATCH":
            serializer = self.get_serializer(tenant, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        serializer = self.get_serializer(tenant)
        return Response(serializer.data)
