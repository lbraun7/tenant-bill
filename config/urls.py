from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import RegisterView
from apps.billing.views import InvoiceViewSet
from apps.plans.views import PlanViewSet
from apps.subscriptions.views import SubscriptionViewSet
from apps.tenants.views import TenantViewSet
from apps.usage.views import CurrentUsageView, UsageEventViewSet
from apps.webhooks.views import StripeWebhookView

router = DefaultRouter()
router.register("plans", PlanViewSet, basename="plan")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("tenants", TenantViewSet, basename="tenant")
router.register("usage-events", UsageEventViewSet, basename="usage-event")


def health_check(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
    path("api/", include(router.urls)),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/usage/", CurrentUsageView.as_view(), name="current-usage"),
    path(
        "api/usage/events/",
        UsageEventViewSet.as_view({"post": "create"}),
        name="usage-event-ingest",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("webhooks/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
