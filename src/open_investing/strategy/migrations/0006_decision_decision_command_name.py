# Generated by Django 5.0.1 on 2024-02-05 13:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strategy", "0005_decision_life_stage_updated_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="decision",
            name="decision_command_name",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
