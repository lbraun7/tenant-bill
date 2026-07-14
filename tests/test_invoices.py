from pathlib import Path
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.billing.models import Invoice
from apps.billing.services import sync_invoice
from apps.billing.tasks import generate_invoice_pdf
from apps.webhooks.models import WebhookEvent
from apps.webhooks.tasks import process_webhook_event
from tests.factories import (
    InvoiceFactory,
    InvoiceLineFactory,
    PlanFactory,
    SubscriptionFactory,
    TenantFactory,
    TenantMembershipFactory,
    UserFactory,
)


@pytest.fixture
def authenticated_client():
    user = UserFactory()
    tenant = TenantFactory()
    TenantMembershipFactory(user=user, tenant=tenant)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, tenant


@pytest.mark.django_db
def test_invoice_list_and_detail_are_isolated_by_current_tenant(authenticated_client):
    client, tenant = authenticated_client
    own = InvoiceFactory(subscription=SubscriptionFactory(plan=PlanFactory(tenant=tenant)))
    InvoiceLineFactory(invoice=own, description="Own line")
    other = InvoiceFactory()

    response = client.get("/api/invoices/")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own.id]
    assert response.json()[0]["lines"][0]["description"] == "Own line"
    assert client.get(f"/api/invoices/{other.id}/").status_code == 404


@pytest.mark.django_db
def test_sync_invoice_persists_status_amounts_and_auditable_lines():
    subscription = SubscriptionFactory(external_subscription_id="sub_invoice_sync")
    payload = {
        "id": "in_sync",
        "number": "INV-SYNC",
        "currency": "usd",
        "total": 6500,
        "subtotal": 6000,
        "tax": 500,
        "amount_paid": 6500,
        "amount_due": 0,
        "lines": {
            "data": [
                {
                    "id": "il_base",
                    "description": "Growth plan",
                    "quantity": 2,
                    "amount": 6000,
                    "currency": "usd",
                    "metadata": {"plan": "growth"},
                }
            ]
        },
    }

    invoice = sync_invoice(subscription, payload, status="paid")
    sync_invoice(subscription, payload, status="paid")

    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.PAID
    assert invoice.total_cents == 6500
    assert invoice.lines.count() == 1
    line = invoice.lines.get()
    assert line.unit_amount_cents == 3000
    assert line.metadata == {"plan": "growth"}


@pytest.mark.django_db(transaction=True)
def test_paid_webhook_syncs_invoice_status_and_enqueues_pdf():
    subscription = SubscriptionFactory(external_subscription_id="sub_webhook_invoice")
    event = WebhookEvent.objects.create(
        provider="stripe",
        external_event_id="evt_invoice_paid_sync",
        event_type="invoice.paid",
        payload={
            "id": "evt_invoice_paid_sync",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_webhook",
                    "subscription": subscription.external_subscription_id,
                    "status": "paid",
                    "currency": "usd",
                    "total": 4900,
                    "amount_paid": 4900,
                    "lines": {"data": []},
                }
            },
        },
    )

    with patch("apps.webhooks.handlers.generate_invoice_pdf.delay") as delay:
        process_webhook_event.run(event.id)

    invoice = Invoice.objects.get(external_invoice_id="in_webhook")
    assert invoice.status == Invoice.Status.PAID
    assert invoice.tenant == subscription.tenant
    delay.assert_called_once_with(invoice.id)


@pytest.mark.django_db
def test_generate_pdf_task_stores_valid_pdf_and_endpoint_serves_it(
    authenticated_client,
    tmp_path,
):
    client, tenant = authenticated_client
    invoice = InvoiceFactory(subscription=SubscriptionFactory(plan=PlanFactory(tenant=tenant)))
    InvoiceLineFactory(invoice=invoice)

    with override_settings(MEDIA_ROOT=tmp_path):
        generate_invoice_pdf.run(invoice.id)
        invoice.refresh_from_db()
        stored_path = Path(invoice.pdf.path)
        assert stored_path.read_bytes().startswith(b"%PDF-")
        assert invoice.pdf_generated_at is not None

        response = client.get(f"/api/invoices/{invoice.id}/pdf/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
