# Generated by Django 5.0 on 2023-12-27 17:41

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="securityoption",
            old_name="s_price",
            new_name="strike_price",
        ),
    ]
