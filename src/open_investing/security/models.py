from django.db import models
from decimal import Decimal
from django.utils import timezone


# from risk_glass.data.data_interface import DefaultDataInterface

# Create your models here.


class SecurityOption(models.Model):
    # data_interface = DefaultDataInterface()

    name = models.CharField(max_length=100, blank=True)
    expire_date = models.DateField(blank=True, null=True)

    security_name = models.CharField(max_length=8, blank=True)
    security_code = models.CharField(max_length=8, blank=True)

    strike_price = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)

    date_time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["security_code", "date_time"],
                name="securityoption_unique_security_code_date_time",
            )
        ]

    @classmethod
    def set_data_interface(cls, new_interface):
        cls.data_interface = new_interface


class SecurityFuture(models.Model):
    # data_interface = DefaultDataInterface()

    name = models.CharField(max_length=100, blank=True)
    expire_date = models.DateField(blank=True, null=True)

    tr_code = models.CharField(max_length=8, blank=True)
    security_name = models.CharField(max_length=8, blank=True)
    security_code = models.CharField(max_length=8, blank=True)

    price = models.DecimalField(max_digits=16, decimal_places=2, default=0.0)

    date_time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["security_code", "date_time"],
                name="securityfuture_unique_security_code_date_time",
            )
        ]

    @classmethod
    def set_data_interface(cls, new_interface):
        cls.data_interface = new_interface
