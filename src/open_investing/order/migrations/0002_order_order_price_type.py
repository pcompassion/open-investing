# Generated by Django 5.0 on 2024-01-06 13:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="order_price_type",
            field=models.CharField(default="market", max_length=32),
            preserve_default=False,
        ),
    ]
