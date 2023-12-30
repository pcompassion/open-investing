from django.db import models
from decimal import Decimal
from django.utils import timezone


# from risk_glass.data.data_interface import DefaultDataInterface

# Create your models here.


class Option(models.Model):
    expire_date = models.DateField(blank=True, null=True)

    security_code = models.CharField(max_length=8, blank=True)

    strike_price = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)

    date_at = models.DateTimeField()
    create_at = models.DateTimeField(auto_now_add=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["security_code", "date_at"],
                name="securityoption_unique_security_code_date_time",
            )
        ]


class Future(models.Model):
    expire_date = models.DateField(blank=True, null=True)

    security_code = models.CharField(max_length=8, blank=True)

    price = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)

    date_at = models.DateTimeField()
    create_at = models.DateTimeField(auto_now_add=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["security_code", "date_at"],
                name="securityfuture_unique_security_code_date_time",
            )
        ]


class NearbyFuture(models.Model):
    expire_date = models.DateField(blank=True, null=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    date_at = models.DateTimeField()
    create_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField(default=list)
