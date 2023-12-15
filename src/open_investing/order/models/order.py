#!/usr/bin/env python3

from django.db import models


class Order(models.Model):

    '''
    https://docs.ccxt.com/#/?id=order-structure
    '''

    order_id = models.CharField(max_length=255, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    security_code = models.CharField(max_length=32, blank=True)

    status = models.CharField(max_length=32, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True)

    data = models.JSONField(default=dict)

    @classmethod
    def set_data_interface(cls, new_interface):
        cls.data_interface = new_interface
