# Generated by Django 5.0.1 on 2024-01-23 07:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0009_alter_order_exchange_order_id_alter_order_life_stage_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="compositeorder",
            name="average_fill_price",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="compositeorder",
            name="filled_quantity",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="compositeorder",
            name="quantity",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="compositeorder",
            name="total_cost",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="order",
            name="average_fill_price",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="order",
            name="filled_quantity",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="order",
            name="price",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="order",
            name="quantity",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="order",
            name="total_cost",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="trade",
            name="price",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
        migrations.AlterField(
            model_name="trade",
            name="quantity",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=16),
        ),
    ]
