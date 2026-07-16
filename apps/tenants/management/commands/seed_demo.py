from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceLine
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.tenants.models import Tenant, TenantMembership
from apps.usage.models import UsageEvent, UsageMetric


class Command(BaseCommand):
    help = "Create or refresh deterministic local demo billing data."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="demo@tenantbill.local")
        parser.add_argument("--password", default="demo-password")

    @transaction.atomic
    def handle(self, *args, **options):
        email = options["email"].lower()
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=email, defaults={"email": email, "first_name": "Demo Owner"}
        )
        if created:
            user.set_password(options["password"])
            user.save(update_fields=("password",))

        tenant, _ = Tenant.objects.update_or_create(
            slug="acme-demo", defaults={"name": "Acme Demo"}
        )
        TenantMembership.objects.update_or_create(
            tenant=tenant,
            user=user,
            defaults={"role": TenantMembership.Role.OWNER, "is_active": True},
        )
        plan, _ = Plan.objects.update_or_create(
            tenant=tenant,
            slug="growth",
            defaults={
                "name": "Growth",
                "description": "Demo recurring plan with metered API usage.",
                "price_cents": 9900,
                "currency": "USD",
                "billing_interval": Plan.BillingInterval.MONTH,
                "included_usage_units": 10_000,
                "metered_unit_name": "request",
                "is_active": True,
            },
        )
        today = timezone.localdate()
        subscription, _ = Subscription.objects.update_or_create(
            external_subscription_id="sub_demo_growth",
            defaults={
                "tenant": tenant,
                "plan": plan,
                "customer_name": "Acme Demo",
                "customer_email": email,
                "status": Subscription.Status.ACTIVE,
                "current_period_start": today,
                "current_period_end": today + timedelta(days=30),
                "external_customer_id": "cus_demo_acme",
            },
        )
        metric, _ = UsageMetric.objects.update_or_create(
            tenant=tenant,
            code="api-requests",
            defaults={
                "name": "API requests",
                "unit_name": "request",
                "stripe_event_name": "api_requests",
                "is_active": True,
            },
        )
        UsageEvent.objects.get_or_create(
            tenant=tenant,
            idempotency_key="demo-usage-001",
            defaults={
                "subscription": subscription,
                "metric": metric,
                "quantity": 1250,
                "metadata": {"source": "seed_demo"},
            },
        )
        invoice, _ = Invoice.objects.update_or_create(
            external_invoice_id="in_demo_001",
            defaults={
                "tenant": tenant,
                "subscription": subscription,
                "number": "DEMO-0001",
                "status": Invoice.Status.PAID,
                "currency": "USD",
                "subtotal_cents": 9900,
                "total_cents": 9900,
                "amount_paid_cents": 9900,
            },
        )
        InvoiceLine.objects.update_or_create(
            invoice=invoice,
            external_line_id="il_demo_growth",
            defaults={
                "description": "Growth plan",
                "quantity": 1,
                "unit_amount_cents": 9900,
                "amount_cents": 9900,
                "currency": "USD",
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Demo data ready for {email} (tenant: acme-demo)."))
