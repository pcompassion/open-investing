# Generated by Django 5.0 on 2024-01-05 06:14

import django.db.models.deletion
import open_investing.strategy.const.decision
import open_investing.strategy.const.strategy
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="StrategySession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("strategy_name", models.CharField(max_length=128)),
                (
                    "life_stage",
                    models.CharField(
                        default=open_investing.strategy.const.strategy.StrategyLifeStage[
                            "Unstarted"
                        ],
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="Decision",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("decision_params", models.JSONField(default=dict)),
                ("quantity", models.FloatField(default=0)),
                ("filled_quantity", models.FloatField(default=0)),
                (
                    "life_stage",
                    models.CharField(
                        default=open_investing.strategy.const.decision.DecisionLifeStage[
                            "Undefined"
                        ],
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "strategy_session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="strategy.strategysession",
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
