#!/usr/bin/env python3
from decimal import Decimal

from django.core import validators
from django.db.models import Field
from open_investing.price.money import Money

from functools import total_ordering
from django.db.models.expressions import Col


@total_ordering
class NonDatabaseFieldBase:
    # https://github.com/mirumee/django-prices/blob/master/django_prices/models.py
    """Base class for all fields that are not stored in the database."""

    empty_values = list(validators.EMPTY_VALUES)

    # Field flags
    auto_created = False
    blank = True
    concrete = False
    editable = False
    unique = False

    is_relation = False
    remote_field = None

    many_to_many = None
    many_to_one = None
    one_to_many = None
    one_to_one = None

    def __init__(self):
        self.column = None
        self.primary_key = False

        self.creation_counter = Field.creation_counter
        Field.creation_counter += 1

    def __eq__(self, other):
        if isinstance(other, (Field, NonDatabaseFieldBase)):
            return self.creation_counter == other.creation_counter
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, (Field, NonDatabaseFieldBase)):
            return self.creation_counter < other.creation_counter
        return NotImplemented

    def __hash__(self):
        return hash(self.creation_counter)

    def contribute_to_class(self, cls, name, **kwargs):
        self.attname = self.name = name
        self.model = cls
        if not hasattr(cls, "_non_database_fields"):
            cls._non_database_fields = {}
        cls._non_database_fields[name] = self
        # cls._meta.add_field(self, private=True)
        setattr(cls, name, self)

    def clean(self, value, model_instance):
        # Shortcircut clean() because Django calls it on all fields with
        # is_relation = False
        return value


class MoneyField(NonDatabaseFieldBase):
    description = (
        "A field that combines an amount of money and currency code into Money"
        "It allows to store prices with different currencies in one database."
    )

    def __init__(
        self,
        amount_field="price_amount",
        currency_field="price_currency",
        verbose_name=None,
        **kwargs
    ):
        super(MoneyField, self).__init__()
        self.amount_field = amount_field
        self.currency_field = currency_field
        self.verbose_name = verbose_name

    def __str__(self):
        return "MoneyField(amount_field=%s, currency_field=%s)" % (
            self.amount_field,
            self.currency_field,
        )

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        amount = getattr(instance, self.amount_field)
        currency = getattr(instance, self.currency_field)
        if amount is not None and currency is not None:
            return Money(amount=amount, currency=currency)
        return self.get_default()

    def __set__(self, instance, value):
        amount = None
        currency = None
        if value is not None:
            amount = value.amount
            currency = value.currency
        setattr(instance, self.amount_field, amount)
        setattr(instance, self.currency_field, currency)

    def get_default(self):
        default_currency = None
        default_amount = Decimal(0)
        if hasattr(self, "model"):
            default_currency = self.model._meta.get_field(
                self.currency_field
            ).get_default()
            default_amount = self.model._meta.get_field(self.amount_field).get_default()

        if default_amount is None:
            return None
        return Money(amount=default_amount, currency=default_currency)
