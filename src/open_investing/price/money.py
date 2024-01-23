#!/usr/bin/env python3

from pydantic import BaseModel
from decimal import Decimal, ROUND_HALF_UP
from typing import ClassVar, overload
from babel.numbers import get_currency_precision

Numeric = int | Decimal


class Money(BaseModel):
    amount: Decimal
    currency: str = "KRW"

    class Config:
        # Convert Decimals to floats for JSON serialization
        json_encoders = {Decimal: lambda v: float(v)}

    def __hash__(self):
        return hash((self.amount, self.currency))

    # def __str__(self):
    #     digits = get_currency_precision(self.currency)
    #     exp = Decimal("0.1") ** digits

    #     rounded_amount = self.amount.quantize(
    #         self.currency_rounding[self.currency], rounding=ROUND_HALF_UP
    #     )
    #     return f"{rounded_amount} {self.currency}"

    def rounded_amount(self):
        # Round the amount based on the currency's rounding rules
        digits = get_currency_precision(self.currency)
        exp = Decimal("0.1") ** digits

        return self.amount.quantize(exp, rounding=rounding)

    def rounded(self) -> "Money":
        amount = self.rounded_amount()

        return Money(amount=amount, currency=self.currency)

    def __repr__(self) -> str:
        return "Money(%r, %r)" % (str(self.amount), self.currency)

    def __lt__(self, other: "Money") -> bool:
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    "Cannot compare amounts in %r and %r"
                    % (self.currency, other.currency)
                )
            return self.amount < other.amount
        return NotImplemented

    def __le__(self, other: "Money") -> bool:
        if self == other:
            return True
        return self < other

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Money):
            return self.amount == other.amount and self.currency == other.currency
        return False

    def __mul__(self, other: Numeric) -> "Money":
        try:
            amount = self.amount * other
        except TypeError:
            return NotImplemented
        return Money(amount=amount, currency=self.currency)

    def __rmul__(self, other: Numeric) -> "Money":
        return self * other

    @overload
    def __truediv__(self, other: "Money") -> Decimal:
        ...  # pragma: no cover

    @overload
    def __truediv__(self, other: Numeric) -> "Money":
        ...  # pragma: no cover

    def __truediv__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError(
                    "Cannot divide amounts in %r and %r"
                    % (self.currency, other.currency)
                )
            return self.amount / other.amount
        try:
            amount = self.amount / other
        except TypeError:
            return NotImplemented
        return Money(amount=amount, currency=self.currency)

    def __add__(self, other: "Money") -> "Money":
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise ValueError(
                    "Cannot add amount in %r to %r" % (self.currency, other.currency)
                )
            amount = self.amount + other.amount
            return Money(amount=amount, currency=self.currency)

        return NotImplemented

    def __sub__(self, other: "Money") -> "Money":
        if isinstance(other, Money):
            if other.currency != self.currency:
                raise ValueError(
                    "Cannot subtract amount in %r from %r"
                    % (other.currency, self.currency)
                )
            amount = self.amount - other.amount
            return Money(amount=amount, currency=self.currency)

        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.amount)
