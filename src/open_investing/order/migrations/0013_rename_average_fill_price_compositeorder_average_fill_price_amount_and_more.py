# Generated by Django 5.0.1 on 2024-01-30 06:21

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0012_order_life_stage_updated_at"),
    ]

    operations = [
        migrations.RenameField(
            model_name="compositeorder",
            old_name="average_fill_price",
            new_name="average_fill_price_amount",
        ),
        migrations.RenameField(
            model_name="compositeorder",
            old_name="total_cost",
            new_name="total_cost_amount",
        ),
    ]
