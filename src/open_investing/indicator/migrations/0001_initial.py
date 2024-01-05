# Generated by Django 5.0 on 2024-01-05 06:14

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MarketIndicator",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=100)),
                (
                    "value",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
                ),
                ("date_at", models.DateTimeField()),
                ("create_at", models.DateTimeField(auto_now_add=True)),
                ("exchange_api_code", models.CharField(blank=True, max_length=32)),
                ("exchange_name", models.CharField(blank=True, max_length=32)),
                ("timeframe", models.DurationField()),
            ],
        ),
    ]
