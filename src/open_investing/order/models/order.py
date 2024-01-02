#!/usr/bin/env python3

from django.db import models


class Order(models.Model):

    """
    https://docs.ccxt.com/#/?id=order-structure
    """

    order_id = models.CharField(max_length=255, blank=True)

    exchange_order_id = models.CharField(max_length=255, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    exchange_api_code = models.CharField(max_length=32, blank=True)

    security_code = models.CharField(max_length=32, blank=True)
    side = models.CharField(max_length=32, blank=True)

    status = models.CharField(max_length=32, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True)

    composite_order = models.ForeignKey(
        "CompositeOrder", on_delete=models.CASCADE, blank=True, null=True
    )

    amount = models.FloatField(default=0)

    data = models.JSONField(default=dict)


class CompositeOrder(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
