# Generated by Django 4.2.6 on 2023-11-17 03:44

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
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
                ("tr_code", models.CharField(blank=True, max_length=8)),
                ("security_name", models.CharField(blank=True, max_length=8)),
                ("security_code", models.CharField(blank=True, max_length=8)),
                (
                    "s_price",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
                ),
                ("date_time", models.DateTimeField(auto_now_add=True)),
                ("create_time", models.DateTimeField(auto_now_add=True)),
                ("data", models.JSONField(default=dict)),
            ],
        ),
        migrations.AddConstraint(
            model_name="securityoption",
            constraint=models.UniqueConstraint(
                fields=("security_code", "date_time"),
                name="risk_glass.data_entity.securityoption_unique_security_code_date_time",
            ),
        ),
    ]
