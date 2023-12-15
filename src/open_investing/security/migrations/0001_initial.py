# Generated by Django 5.0 on 2023-12-15 14:11

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MarketIndicatorDay",
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
                ("date", models.DateField()),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("exchange_api_code", models.CharField(blank=True, max_length=32)),
                ("exchange_name", models.CharField(blank=True, max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name="SecurityFuture",
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
                ("expire_date", models.DateField(blank=True, null=True)),
                ("tr_code", models.CharField(blank=True, max_length=8)),
                ("security_name", models.CharField(blank=True, max_length=8)),
                ("security_code", models.CharField(blank=True, max_length=8)),
                (
                    "price",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
                ),
                ("date_time", models.DateTimeField()),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("exchange_api_code", models.CharField(blank=True, max_length=32)),
                ("exchange_name", models.CharField(blank=True, max_length=32)),
                ("data", models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name="SecurityOption",
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
                ("expire_date", models.DateField(blank=True, null=True)),
                ("security_name", models.CharField(blank=True, max_length=8)),
                ("security_code", models.CharField(blank=True, max_length=8)),
                (
                    "s_price",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
                ),
                ("date_time", models.DateTimeField()),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("exchange_api_code", models.CharField(blank=True, max_length=32)),
                ("exchange_name", models.CharField(blank=True, max_length=32)),
                ("data", models.JSONField(default=dict)),
            ],
        ),
        migrations.AddConstraint(
            model_name="marketindicatorday",
            constraint=models.UniqueConstraint(
                fields=("name", "date"), name="unique_name_date"
            ),
        ),
        migrations.AddConstraint(
            model_name="securityfuture",
            constraint=models.UniqueConstraint(
                fields=("security_code", "date_time"),
                name="securityfuture_unique_security_code_date_time",
            ),
        ),
        migrations.AddConstraint(
            model_name="securityoption",
            constraint=models.UniqueConstraint(
                fields=("security_code", "date_time"),
                name="securityoption_unique_security_code_date_time",
            ),
        ),
    ]
