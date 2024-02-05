#!/usr/bin/env python3

from decimal import Decimal
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

    quantity_multiplier = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("1")
    )

    quantity_order = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )

    quantity_exposure = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )

    filled_quantity_order = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0")
    )
    filled_quantity_exposure = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0")
    )

    life_stage = models.CharField(
        max_length=32, default=DecisionLifeStage.Undefined, db_index=True
    )
    life_stage_updated_at = models.DateTimeField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def update_fill(self, fill_quantity_order):
        # Update total cost and filled quantity

        self.filled_quantity_order += fill_quantity_order
        self.filled_quantity_exposure = (
            self.filled_quantity_order * self.quantity_multiplier
        )

    def is_fullfilled(self):
        return self.filled_quantity_order >= self.quantity_order

    def set_quantity(self):
        if self.quantity_order is None and self.quantity_exposure is not None:
            self.quantity_order = self.quantity_exposure / self.quantity_multiplier
        elif self.quantity_exposure is None and self.quantity_order is not None:
            self.quantity_exposure = self.quantity_order * self.quantity_multiplier

    def save(self, *args, **kwargs):
        self.set_quantity()

        if self.quantity_order is not None and self.quantity_exposure is not None:
            if self.quantity_order * self.quantity_multiplier != self.quantity_exposure:
                raise ValueError(
                    "quantity_order * self.quantity_multiplier != self.quantity_exposure"
                )
        super().save(*args, **kwargs)
