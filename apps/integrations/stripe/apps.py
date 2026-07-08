from django.apps import AppConfig


class StripeIntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "stripe_integration"
    name = "apps.integrations.stripe"
