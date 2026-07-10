from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.tenants.permissions import HasCurrentTenant
from apps.usage.models import UsageEvent
from apps.usage.serializers import UsageEventSerializer


class UsageEventViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UsageEventSerializer
    permission_classes = (IsAuthenticated, HasCurrentTenant)
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return UsageEvent.objects.select_related("subscription", "tenant").filter(
            tenant=self.request.current_tenant
        )
