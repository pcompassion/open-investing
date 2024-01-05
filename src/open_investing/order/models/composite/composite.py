#!/usr/bin/env python3


import uuid
from django.db import models


class CompositeOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    order_type = models.CharField(max_length=32)
    strategy_session = models.ForeignKey(
        "strategy.StrategySession", on_delete=models.CASCADE, blank=True, null=True
    )
    decision = models.ForeignKey(
        "strategy.Decision", on_delete=models.CASCADE, blank=True, null=True
    )

    quantity = models.FloatField(default=0)
    filled_quantity = models.FloatField(default=0)

    average_fill_price = models.FloatField(default=0)
    total_cost = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)

    def update_fill(self, fill_quantity, fill_price):
        # order_type = self.order_type
        # match order_type:
        #     case OrderType.BestMarketIceberg:

        # Update total cost and filled quantity
        new_cost = fill_quantity * fill_price
        self.total_cost += new_cost
        self.filled_quantity += fill_quantity

        # Update average fill price
        if self.filled_quantity > 0:
            self.average_fill_price = self.total_cost / self.filled_quantity

    def subtract_quantity(self, quantity):
        self.quantity -= quantity
