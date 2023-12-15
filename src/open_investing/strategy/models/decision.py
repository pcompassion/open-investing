#!/usr/bin/env python3

from django.db import models

import uuid


class Decision(models.Model):
    """
    collection of orders
    and the execution condition of orders


    order: {side, type, }


    """

    strategy_id = models.UUIDField()
    strategy_name = models.CharField(max_length=128)

    decision_type = models.CharField(max_length=128)
    decision_params = models.JSONField(default=dict)

    life_stage = models.CharField(max_length=128)

    amount = models.FloatField(default=0)
    filled_amount = models.FloatField(default=0)
    remaining_amount = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.life_stage = DecisionLifeStage.UNOPENED
