# Generated by Django 5.0.1 on 2024-02-21 03:06

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "order",
            "0023_alter_compositeorderoffsetrelation_filled_quantity_order_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="leader_follower_ratio",
            new_name="leader_quantity_order",
        ),
    ]