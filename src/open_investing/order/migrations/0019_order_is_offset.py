# Generated by Django 5.0.1 on 2024-02-05 07:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0018_compositeorder_is_offset"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="is_offset",
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]