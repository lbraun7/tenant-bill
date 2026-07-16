from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.plans.models import Plan
from apps.plans.serializers import PlanSerializer
from apps.tenants.permissions import HasCurrentTenant


class PlanViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Plan.objects.none()
    serializer_class = PlanSerializer
    permission_classes = (IsAuthenticated, HasCurrentTenant)
    lookup_field = "slug"
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return Plan.objects.filter(tenant=self.request.current_tenant)
