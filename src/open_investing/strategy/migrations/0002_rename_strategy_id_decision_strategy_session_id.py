# Generated by Django 5.0 on 2023-12-29 07:25

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("strategy", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="decision",
            old_name="strategy_id",
            new_name="strategy_session_id",
        ),
    ]
