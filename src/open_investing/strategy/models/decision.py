#!/usr/bin/env python3

from django.db import models

import uuid
from open_investing.strategy.const.decision import DecisionLifeStage


class Decision(models.Model):
    """
    collection of orders
    and the execution condition of orders
    order: {side, type, }

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    strategy_session = models.ForeignKey(
        "strategy.StrategySession", on_delete=models.CASCADE
    )

    # decision_type = models.CharField(max_length=128)
    decision_params = models.JSONField(default=dict)

    amount = models.FloatField(default=0)
    filled_amount = models.FloatField(default=0)
    remaining_amount = models.FloatField(default=0)

    life_stage = models.CharField(max_length=32, default=DecisionLifeStage.Unstarted)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.life_stage = DecisionLifeStage.Unopened
