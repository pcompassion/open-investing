# Generated by Django 5.0 on 2023-12-30 06:37

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0004_rename_securityfuture_future_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="future",
            name="name",
        ),
        migrations.RemoveField(
            model_name="future",
            name="security_name",
        ),
        migrations.RemoveField(
            model_name="option",
            name="name",
        ),
        migrations.RemoveField(
            model_name="option",
            name="security_name",
        ),
    ]
