# Generated by Django 5.0.1 on 2024-01-22 08:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0011_alter_option_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="future",
            name="derivative_type",
            field=models.CharField(db_index=True, default="Future", max_length=16),
            preserve_default=False,
        ),
    ]
