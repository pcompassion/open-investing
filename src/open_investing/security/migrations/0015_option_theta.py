# Generated by Django 5.0.1 on 2024-01-29 08:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0014_option_delta"),
    ]

    operations = [
        migrations.AddField(
            model_name="option",
            name="theta",
            field=models.DecimalField(
                db_index=True, decimal_places=2, default=0.0, max_digits=16
            ),
        ),
    ]
