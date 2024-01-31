#!/usr/bin/env python3
from decimal import Decimal
from django.db import models


class MarketIndicator(models.Model):
    name = models.CharField(max_length=100, blank=True)
    value = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal("0"))

    date_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    class Meta:
        pass
