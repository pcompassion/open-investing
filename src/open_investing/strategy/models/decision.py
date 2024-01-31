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

    quantity_order = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    filled_quantity_order = models.DecimalField(
        max_digits=16, decimal_places=2, default=0.0
    )

    life_stage = models.CharField(
        max_length=32, default=DecisionLifeStage.Undefined, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update_fill(self, fill_quantity_order):
        # Update total cost and filled quantity

        self.filled_quantity_order += fill_quantity_order

    def is_fullfilled(self):
        return self.filled_quantity_order >= self.quantity_order
