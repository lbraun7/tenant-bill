from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0001_initial")]

    operations = [
        migrations.AddConstraint(
            model_name="subscription",
            constraint=models.UniqueConstraint(
                condition=~models.Q(external_subscription_id=""),
                fields=("external_subscription_id",),
                name="unique_non_empty_external_subscription_id",
            ),
        ),
    ]
