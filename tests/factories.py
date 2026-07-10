import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.tenants.models import Tenant, TenantMembership
from apps.usage.models import UsageEvent


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}@example.com")
    email = factory.SelfAttribute("username")
    first_name = factory.Faker("first_name")
    password = factory.PostGenerationMethodCall("set_password", "password123")


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Sequence(lambda n: f"Tenant {n}")
    slug = factory.Sequence(lambda n: f"tenant-{n}")


class TenantMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TenantMembership

    tenant = factory.SubFactory(TenantFactory)
    user = factory.SubFactory(UserFactory)
    role = TenantMembership.Role.MEMBER


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plan

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Plan {n}")
    slug = factory.Sequence(lambda n: f"plan-{n}")
    price_cents = 4900
    currency = "USD"
    billing_interval = Plan.BillingInterval.MONTH
    included_usage_units = 1000
    metered_unit_name = "api_call"


class SubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subscription

    tenant = factory.SelfAttribute("plan.tenant")
    plan = factory.SubFactory(PlanFactory)
    customer_name = factory.Sequence(lambda n: f"Customer {n}")
    customer_email = factory.Sequence(lambda n: f"customer{n}@example.com")
    status = Subscription.Status.ACTIVE
    current_period_start = factory.LazyFunction(timezone.localdate)
    current_period_end = factory.LazyAttribute(
        lambda _subscription: timezone.localdate() + timezone.timedelta(days=30)
    )


class UsageEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UsageEvent

    tenant = factory.SelfAttribute("subscription.tenant")
    subscription = factory.SubFactory(SubscriptionFactory)
    quantity = 10
    occurred_at = factory.LazyFunction(timezone.now)
    metadata = factory.Dict({})
