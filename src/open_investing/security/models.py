from django.db import models
from open_investing.price.money import Money
from decimal import Decimal
from django.utils import timezone
from open_investing.price.money_field import MoneyField


# from risk_glass.data.data_interface import DefaultDataInterface

# Create your models here.


class Option(models.Model):
    expire_at = models.DateTimeField(blank=True, null=True, db_index=True)

    security_code = models.CharField(max_length=10, db_index=True)
    derivative_type = models.CharField(max_length=16, db_index=True)

    currency = models.CharField(max_length=3, default="KRW")

    strike_price_amount = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0')
    )
    strike_price = MoneyField(
        amount_field="strike_price_amount", currency_field="currency"
    )

    price_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0'))
    price = MoneyField(amount_field="price_amount", currency_field="currency")

    strike_price_amount = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0')
    )

    delta = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0'), db_index=True
    )
    theta = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal('0'), db_index=True
    )

    date_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

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

    # @property
    # def strike_price(self):
    #     return Money(amount=self.strike_price_amount, currency=self.currency)

    # @strike_price.setter
    # def strike_price(self, value):
    #     self.strike_price_amount = value.amount
    #     self.currency = value.currency

    # @property
    # def price(self):
    #     return Money(amount=self.price_amount, currency=self.currency)

    # @price.setter
    # def price(self, value):
    #     self.price_amount = value.amount
    #     self.currency = value.currency


class Future(models.Model):
    expire_at = models.DateTimeField(blank=True, null=True, db_index=True)
    currency = models.CharField(max_length=3, default="KRW")

    security_code = models.CharField(max_length=8, db_index=True)
    price_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0'))
    price = MoneyField(amount_field="price_amount", currency_field="currency")
    derivative_type = models.CharField(max_length=16, db_index=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    date_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["security_code", "date_at"],
                name="securityfuture_unique_security_code_date_time",
            )
        ]

    # @property
    # def price(self):
    #     return Money(amount=self.price_amount, currency=self.currency)

    # @price.setter
    # def price(self, value):
    #     self.price_amount = value.amount
    #     self.currency = value.currency


class NearbyFuture(models.Model):
    expire_at = models.DateTimeField(blank=True, null=True, db_index=True)
    currency = models.CharField(max_length=3, default="KRW")

    security_code = models.CharField(max_length=8, db_index=True)
    price_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0'))
    price = MoneyField(amount_field="price_amount", currency_field="currency")
    derivative_type = models.CharField(max_length=16, db_index=True)

    exchange_api_code = models.CharField(max_length=32, blank=True)
    exchange_name = models.CharField(max_length=32, blank=True)
    timeframe = models.DurationField()

    date_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField(default=list)


class Quote(models.Model):
    security_code = models.CharField(max_length=8, db_index=True)
    date_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["security_code", "date_at"],
                name="securityquote_unique_security_code_date_time",
            )
        ]
