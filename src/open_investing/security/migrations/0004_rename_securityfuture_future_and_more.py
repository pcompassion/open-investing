# Generated by Django 5.0 on 2023-12-29 14:21

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0003_nearbyfuture_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="SecurityFuture",
            new_name="Future",
        ),
        migrations.RenameModel(
            old_name="SecurityOption",
            new_name="Option",
        ),
    ]
