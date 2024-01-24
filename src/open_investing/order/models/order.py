#!/usr/bin/env python3

from open_investing.price.money import Money

from open_investing.order.const.order import OrderSide
import uuid
from open_investing.order.const.order import OrderLifeStage
from django.db import models
from open_investing.price.money_field import MoneyField


class Order(models.Model):

    """
    https://docs.ccxt.com/#/?id=order-structure
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_type = models.CharField(max_length=32, db_index=True)
    order_price_type = models.CharField(max_length=32)

    exchange_order_id = models.CharField(
        max_length=255, blank=True, null=False, default="", db_index=True
    )
    security_code = models.CharField(max_length=32, blank=True, db_index=True)
    side = models.CharField(max_length=32, blank=True)

    life_stage = models.CharField(
        max_length=32, blank=True, default=OrderLifeStage.Undefined, db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    date_at = models.DateTimeField(null=True)

    parent_order = models.ForeignKey(
        "order.CompositeOrder", on_delete=models.CASCADE, blank=True, null=True
    )

    strategy_session = models.ForeignKey(
        "strategy.StrategySession", on_delete=models.CASCADE, blank=True, null=True
    )

    decision = models.ForeignKey(
        "strategy.Decision", on_delete=models.CASCADE, blank=True, null=True
    )
    currency = models.CharField(max_length=3, default="KRW")

    price_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    price = MoneyField(amount_field="price_amount", currency_field="currency")

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

    exchange_name = models.CharField(max_length=32, blank=True)
    exchange_api_code = models.CharField(max_length=32, blank=True)

    data = models.JSONField(default=dict)

    offsetted_by_me = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="order.OrderOffsetRelation",
        through_fields=("offsetting_order", "offsetted_order"),
        related_name="offsetting_me",
    )

    def update_fill(self, fill_quantity, fill_price):
        # Update total cost and filled quantity
        new_cost = fill_quantity * fill_price
        self.total_cost += new_cost
        self.filled_quantity += fill_quantity

        # Update average fill price
        if self.filled_quantity > 0:
            self.average_fill_price = self.total_cost / self.filled_quantity

        if self.life_stage == OrderLifeStage.Undefined:
            self.life_stage = OrderLifeStage.Opened

    def calculate_roi(self, current_price):
        """
        Calculates the return on investment (ROI) based on the current price.
        """

        if self.filled_quantity == 0:
            return 0  # If nothing has been filled, ROI is 0

        invested = self.average_fill_price * self.filled_quantity
        current_value = current_price * self.filled_quantity
        return (current_value - invested) / invested

    def is_filled(self):
        return self.filled_quantity >= self.quantity

    def subtract_quantity(self, quantity):
        self.quantity -= quantity

    def calculate_pnl(self, current_price):
        if self.filled_quantity == 0:
            return Money(amount=0, currency=current_price.currency)

        current_value = current_price * self.filled_quantity

        if self.side == OrderSide.Buy:
            return current_value - self.total_cost
        elif self.side == OrderSide.Sell:
            return self.total_cost - current_value

    def get_offsetted_orders(self):
        """
        Returns a queryset of Orders that this Order offsets
        """
        return self.offsetted_by_me.all()

    def get_offsetting_orders(self):
        """
        Returns a queryset of Orders that offset this Order
        """
        return self.offsetting_me.all()


class Trade(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date_at = models.DateTimeField()

    quantity = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)

    currency = models.CharField(max_length=3, default="KRW")

    price_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)
    price = MoneyField(amount_field="price_amount", currency_field="currency")


class OrderEventEntry(models.Model):

    """

    exchange.place_request
    exchange.place_success / failure

    exchange.filled
    exchange.cancelled

    filled
    """

    order = models.ForeignKey(
        "order.Order", on_delete=models.CASCADE, blank=True, null=True
    )
    composite_order = models.ForeignKey(
        "order.CompositeOrder", on_delete=models.CASCADE, blank=True, null=True
    )
    trade = models.ForeignKey("Trade", on_delete=models.CASCADE, blank=True, null=True)

    event_name = models.CharField(max_length=32, blank=True)

    date_at = models.DateTimeField()
    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
