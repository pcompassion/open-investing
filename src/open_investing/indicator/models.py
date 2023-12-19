#!/usr/bin/env python3
from django.db import models


class MarketIndicator(models.Model):
    name = models.CharField(max_length=100, blank=True)
    value = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)

    date_at = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "date"], name="unique_name_date")
        ]
