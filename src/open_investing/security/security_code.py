#!/usr/bin/env python3
from enum import Enum, auto
import calendar
from typing import Any, Dict, Optional, Callable, Awaitable
import copy
import pandas as pd
import pendulum


class DerivativeType(Enum):
    FUTURE = "101"
    MFUTURE = "105"
    CALL = "201"
    PUT = "301"


class DerivativeCode:
    MONTH_MAP = {
        1: "1",
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "A",
        11: "B",
        12: "C",
    }

    BASE_YEAR = 2004
    BASE_YEAR_STR = "A"

    tz = "Asia/Seoul"

    def __init__(
        self, derivative_type: DerivativeType, year: int, month: int, strike_price: int
    ):
        self.derivative_type = derivative_type
        if type(self.derivative_type) != DerivativeType:
            print("wrong")

        self.year = year
        self.month = month
        self.strike_price = strike_price

    @classmethod
    def from_string(cls, code_str, strike_price: Optional[float] = None):
        derivative_type = DerivativeType(code_str[:3])
        year_str = code_str[3]
        month_str = code_str[4]
        if strike_price is None:
            strike_price = float(code_str[5:])
        strike_price = float(strike_price)

        year = cls.year_from_str(year_str)

        month = None
        for k, v in cls.MONTH_MAP.items():
            if v == month_str:
                month = k
                break

        return cls(derivative_type, year, month, strike_price)

    def __str__(self):
        return f"{self.derivative_type.value}{self.year_str}{self.month_str}{int(self.strike_price)}"

    def copy(self):
        return copy.deepcopy(self)

    @property
    def month_str(self):
        return self.MONTH_MAP.get(self.month, "Invalid Month")

    @month_str.setter
    def month_str(self, value):
        for k, v in self.MONTH_MAP.items():
            if v == value:
                self.month = k
                return
        raise ValueError("Invalid month string")

    @property
    def year_str(self):
        year_offset = self.year - self.BASE_YEAR
        return chr(ord(self.BASE_YEAR_STR) + year_offset)

    @classmethod
    def year_from_str(cls, char):
        year_offset = ord(char) - ord(cls.BASE_YEAR_STR)
        return cls.BASE_YEAR + year_offset

    @year_str.setter
    def year_str(self, value):
        self.year = self.year_from_str(value)

    def as_derivative_type_str(
        self, derivative_type: DerivativeType, strike_price: Optional[float] = None
    ):
        if strike_price is None:
            strike_price = self.strike_price
        return (
            f"{derivative_type.value}{self.year_str}{self.month_str}{int(strike_price)}"
        )

    def clone_as_derivative_type(
        self, derivative_type: DerivativeType, strike_price: Optional[float] = None
    ):
        if strike_price is None:
            strike_price = self.strike_price

        new_instance = self.copy()

        new_instance.derivative_type = derivative_type
        new_instance.strike_price = strike_price

        return new_instance

    @classmethod
    def strike_price_from_string(cls, code_str):
        code = cls.from_string(code_str)

        return code.strike_price

    @property
    def name(self):
        return f"{self.derivative_type.value}{self.year_str}{self.month_str}"

    @property
    def future_name(self):
        return f"{self.derivative_type.value}{self.year_str}{self.month_str}000"

    @classmethod
    def get_name_and_strike_price(cls, code_str):
        code = cls.from_string(code_str)
        return pd.Series([code.name, int(code.strike_price)])

    @classmethod
    def get_fields(cls, code_str, field_names):
        code = cls.from_string(code_str)

        l = []

        for field_name in field_names:
            match field_name:
                case "name":
                    l.append(code.name)
                case "strike_price":
                    l.append(float(code.strike_price))
                case "expire_date":
                    l.append(code.expire_date)

        return pd.Series(l)

    @property
    def expire_date(self):
        dt = pendulum.datetime(self.year, self.month, 1, tz=self.tz)
        return dt.date()

    def to_dict(self):
        return self.__dict__
