from django.http import FileResponse, Http404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from apps.billing.models import Invoice
from apps.billing.serializers import InvoiceSerializer
from apps.tenants.permissions import HasCurrentTenant


class InvoiceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Invoice.objects.none()
    serializer_class = InvoiceSerializer
    permission_classes = (IsAuthenticated, HasCurrentTenant)
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return (
            Invoice.objects.select_related("tenant", "subscription")
            .prefetch_related("lines")
            .filter(tenant=self.request.current_tenant)
        )

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        if not invoice.pdf:
            raise Http404("Invoice PDF has not been generated yet.")
        return FileResponse(
            invoice.pdf.open("rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"invoice-{invoice.number or invoice.pk}.pdf",
        )
