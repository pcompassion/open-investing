#!/usr/bin/env python3

import uuid
from django.db import models


class Order(models.Model):

    """
    https://docs.ccxt.com/#/?id=order-structure
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_type = models.CharField(max_length=32)

    exchange_order_id = models.CharField(max_length=255, blank=True)
    security_code = models.CharField(max_length=32, blank=True)
    side = models.CharField(max_length=32, blank=True)

    status = models.CharField(max_length=32, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    date_at = models.DateTimeField(null=True)

    parent_order = models.ForeignKey(
        "CompositeOrder", on_delete=models.CASCADE, blank=True, null=True
    )
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

    exchange_name = models.CharField(max_length=32, blank=True)
    exchange_api_code = models.CharField(max_length=32, blank=True)

    data = models.JSONField(default=dict)

    def update_fill(self, fill_quantity, fill_price):
        # Update total cost and filled quantity
        new_cost = fill_quantity * fill_price
        self.total_cost += new_cost
        self.filled_quantity += fill_quantity

        # Update average fill price
        if self.filled_quantity > 0:
            self.average_fill_price = self.total_cost / self.filled_quantity

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


class Trade(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date_at = models.DateTimeField()

    quantity = models.FloatField(default=0)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    price = models.FloatField()


class OrderEvent(models.Model):

    """

    exchange.place_request
    exchange.place_success / failure

    exchange.filled
    exchange.cancelled

    filled
    """

    order = models.ForeignKey("Order", on_delete=models.CASCADE, blank=True, null=True)
    parent_order = models.ForeignKey(
        "CompositeOrder", on_delete=models.CASCADE, blank=True, null=True
    )
    trade = models.ForeignKey("Trade", on_delete=models.CASCADE, blank=True, null=True)

    event_name = models.CharField(max_length=32, blank=True)

    date_at = models.DateTimeField()
    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
