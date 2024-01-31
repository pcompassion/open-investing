#!/usr/bin/env python3


from decimal import Decimal
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

    currency = models.CharField(max_length=3, default="KRW")

    average_fill_price_amount = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0")
    )
    average_fill_price = MoneyField(
        amount_field="average_fill_price_amount", currency_field="currency"
    )

    total_cost_amount = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0")
    )
    total_cost = MoneyField(amount_field="total_cost_amount", currency_field="currency")

    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)

    def update_fill(self, fill_quantity_order, fill_price):
        # Update total cost and filled quantity
        new_cost = fill_quantity_order * self.quantity_multiplier * fill_price
        self.total_cost += new_cost
        self.filled_quantity_order += fill_quantity_order
        self.filled_quantity_exposure = (
            self.filled_quantity_order * self.quantity_multiplier
        )
        # Update average fill price
        if self.filled_quantity_order > 0:
            self.average_fill_price = self.total_cost / self.filled_quantity_exposure

        if self.life_stage == OrderLifeStage.Undefined:
            self.life_stage = OrderLifeStage.Opened

    def subtract_quantity(self, quantity_order):
        self.quantity_order -= quantity_order
        self.quantity_exposure -= quantity_order * self.quantity_multiplier

    def set_quantity(self):
        if self.quantity_order is None:
            self.quantity_order = self.quantity_exposure / self.quantity_multiplier
        elif self.quantity_exposure is None:
            self.quantity_exposure = self.quantity_order * self.quantity_multiplier

    def save(self, *args, **kwargs):
        self.set_quantity()

        if self.quantity_order is None:
            raise ValueError("quantity_order is None")
        if self.quantity_exposure is None:
            raise ValueError("quantity_exposure is None")

        if self.quantity_order * self.quantity_multiplier != self.quantity_exposure:
            raise ValueError(
                "quantity_order * self.quantity_multiplier != self.quantity_exposure"
            )
        super(CompositeOrder, self).save(*args, **kwargs)

    # @classmethod
    # def create_order(cls, quantity_order=None, quantity_exposure=)
