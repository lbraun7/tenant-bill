from django.db.models import Sum
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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


class CurrentUsageView(APIView):
    permission_classes = (IsAuthenticated, HasCurrentTenant)

    def get(self, request):
        subscriptions = request.current_tenant.subscriptions.filter(
            status__in=("active", "trialing")
        ).select_related("plan")
        result = []
        for subscription in subscriptions:
            events = UsageEvent.objects.filter(
                tenant=request.current_tenant,
                subscription=subscription,
                occurred_at__date__gte=subscription.current_period_start,
                occurred_at__date__lt=subscription.current_period_end,
            )
            metrics = [
                {
                    "metric_id": row["metric_id"],
                    "metric_code": row["metric__code"],
                    "quantity": row["quantity"],
                }
                for row in events.values("metric_id", "metric__code")
                .annotate(quantity=Sum("quantity"))
                .order_by("metric__code")
            ]
            result.append(
                {
                    "subscription_id": subscription.id,
                    "period_start": subscription.current_period_start,
                    "period_end": subscription.current_period_end,
                    "included_units": subscription.plan.included_usage_units,
                    "total_quantity": sum(item["quantity"] for item in metrics),
                    "metrics": metrics,
                }
            )
        return Response(result, status=status.HTTP_200_OK)
