# Generated by Django 5.0.1 on 2024-01-18 07:30

import open_investing.strategy.const.decision
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strategy", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="decision",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="decision",
            name="life_stage",
            field=models.CharField(
                db_index=True,
                default=open_investing.strategy.const.decision.DecisionLifeStage[
                    "Undefined"
                ],
                max_length=32,
            ),
        ),
    ]
