#!/usr/bin/env python3

from django.db import models


class Order(models.Model):

    """
    https://docs.ccxt.com/#/?id=order-structure
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    exchange_order_id = models.CharField(max_length=255, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    exchange_api_code = models.CharField(max_length=32, blank=True)

    security_code = models.CharField(max_length=32, blank=True)
    side = models.CharField(max_length=32, blank=True)

    status = models.CharField(max_length=32, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    date_at = models.DateTimeField(null=True)

    composite_order = models.ForeignKey(
        "CompositeOrder", on_delete=models.CASCADE, blank=True, null=True
    )

    quantity = models.FloatField(default=0)
    filled_quantity = models.FloatField(default=0)

    data = models.JSONField(default=dict)


class CompositeOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    order_type = models.CharField(max_length=32)
    data = models.JSONField(default=dict)

    quantity = models.FloatField(default=0)
    filled_quantity = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)


class Trade(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    date_at = models.DateTimeField()

    quantity = models.FloatField(default=0)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    price = models.FloatField()


class OrderEvent(moels.Model):

    """
    placed
    filled
    modified
    cancelled
    """

    order = models.ForeignKey("Order", on_delete=models.CASCADE, blank=True, null=True)
    composite_order = models.ForeignKey(
        "CompositeOrder", on_delete=models.CASCADE, blank=True, null=True
    )
    trade = models.ForeignKey("Trade", on_delete=models.CASCADE, blank=True, null=True)

    event_name = models.CharField(max_length=32, blank=True)

    date_at = models.DateTimeField()
    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
