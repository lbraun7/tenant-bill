import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("usage", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="UsageMetric",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("code", models.SlugField(max_length=120)),
                ("unit_name", models.CharField(max_length=80)),
                ("stripe_event_name", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage_metrics",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={"ordering": ("name", "id")},
        ),
        migrations.AddConstraint(
            model_name="usagemetric",
            constraint=models.UniqueConstraint(
                fields=("tenant", "code"), name="unique_usage_metric_code"
            ),
        ),
        migrations.AddField(
            model_name="usageevent",
            name="metric",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="events",
                to="usage.usagemetric",
            ),
        ),
        migrations.AddField(
            model_name="usageevent",
            name="sync_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("synced", "Synced"), ("failed", "Failed")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="usageevent",
            name="synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="usageevent", name="sync_error", field=models.TextField(blank=True)
        ),
    ]
