# Generated by Django 5.0.1 on 2024-02-05 05:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strategy", "0004_decision_filled_quantity_exposure_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="decision",
            name="life_stage_updated_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
