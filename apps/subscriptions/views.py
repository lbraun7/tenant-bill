from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.subscriptions.models import Subscription
from apps.subscriptions.serializers import SubscriptionSerializer
from apps.tenants.permissions import HasCurrentTenant


class SubscriptionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated, HasCurrentTenant)
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return Subscription.objects.select_related("plan", "tenant").filter(
            tenant=self.request.current_tenant
        )
