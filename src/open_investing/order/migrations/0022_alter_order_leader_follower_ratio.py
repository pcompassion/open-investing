# Generated by Django 5.0.1 on 2024-02-20 13:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0021_order_leader_follower_ratio"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="leader_follower_ratio",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=16, null=True
            ),
        ),
    ]
