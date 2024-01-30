#!/usr/bin/env python3


import uuid
from django.db import models
from open_investing.order.const.order import OrderLifeStage
from open_investing.price.money_field import MoneyField


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
    life_stage = models.CharField(
        max_length=32, blank=True, default=OrderLifeStage.Undefined
    )

    quantity = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    filled_quantity = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)

    average_fill_price_amount = models.DecimalField(
        max_digits=16, decimal_places=2, default=0.0
    )
    average_fill_price = MoneyField(
        amount_field="average_fill_price_amount", currency_field="currency"
    )

    total_cost_amount = models.DecimalField(
        max_digits=16, decimal_places=2, default=0.0
    )
    total_cost = MoneyField(amount_field="total_cost_amount", currency_field="currency")

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
        if self.life_stage == OrderLifeStage.Undefined:
            self.life_stage = OrderLifeStage.Opened

    def subtract_quantity(self, quantity):
        self.quantity -= quantity
