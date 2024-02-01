# Generated by Django 5.0.1 on 2024-01-31 08:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "order",
            "0015_rename_filled_quantity_compositeorder_filled_quantity_order_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="trade",
            old_name="quantity",
            new_name="quantity_order",
        ),
        migrations.AddField(
            model_name="trade",
            name="quantity_multiplier",
            field=models.DecimalField(decimal_places=2, default=1, max_digits=16),
        ),
    ]