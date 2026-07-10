import factory
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, TenantMembership


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
