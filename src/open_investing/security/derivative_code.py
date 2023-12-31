#!/usr/bin/env python3
from enum import Enum, auto
import calendar
from pendulum import Time
from typing import Any, Dict, Optional, Callable, Awaitable
import copy
import pandas as pd
import pendulum
from open_library.time.calendar import find_nth_weekday_of_month
from open_investing.const.code_name import DerivativeType


class DerivativeTypeCode(str, Enum):
    Future = "101"
    MiniFuture = "105"
    Call = "201"
    Put = "301"


name_to_code_map = {
    DerivativeType.Future: DerivativeTypeCode.Future,
    DerivativeType.MiniFuture: DerivativeTypeCode.MiniFuture,
    DerivativeType.Call: DerivativeTypeCode.Call,
    DerivativeType.Put: DerivativeTypeCode.Put,
}


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
        self,
        derivative_type_code: DerivativeTypeCode | DerivativeType,
        year: int,
        month: int,
        strike_price: float,
        **kwargs,
    ):
        if isinstance(derivative_type_code, DerivativeType):
            derivative_type_code = get_derivative_code_from_type(derivative_type_code)

        self.derivative_type_code = derivative_type_code

        self.year = year
        self.month = month
        self.strike_price = strike_price

        derivative_type = self.get_derivative_type_from_code(derivative_type_code)
        self.derivative_type = derivative_type

    @classmethod
    def from_string(cls, code_str, strike_price: Optional[float] = None):
        derivative_type_code = DerivativeTypeCode(code_str[:3])
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

        if month is None:
            raise ValueError(f"Invalid month_str: {month_str}")

        return cls(derivative_type_code, year, month, strike_price)

    def __str__(self):
        return f"{self.derivative_type_code}{self.year_str}{self.month_str}{int(self.strike_price)}"

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

    def as_derivative_type_code_str(
        self,
        derivative_type_code: DerivativeTypeCode,
        strike_price: Optional[float] = None,
    ):
        if strike_price is None:
            strike_price = self.strike_price
        return (
            f"{derivative_type_code}{self.year_str}{self.month_str}{int(strike_price)}"
        )

    def clone_as_derivative_type_code(
        self,
        derivative_type_code: DerivativeTypeCode,
        strike_price: Optional[float] = None,
    ):
        if strike_price is None:
            strike_price = self.strike_price

        new_instance = self.copy()

        new_instance.derivative_type_code = derivative_type_code
        new_instance.strike_price = strike_price

        return new_instance

    @classmethod
    def strike_price_from_string(cls, code_str):
        code = cls.from_string(code_str)

        return code.strike_price

    @property
    def name(self):
        if self.derivative_type_code in [
            DerivativeTypeCode.Future,
            DerivativeTypeCode.MiniFuture,
        ]:
            return self.future_name
        return f"{self.derivative_type_code}{self.year_str}{self.month_str}"

    @property
    def future_name(self):
        return f"{self.derivative_type_code}{self.year_str}{self.month_str}000"

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
                case "expire_at":
                    l.append(code.expire_at)

        return pd.Series(l)

    @property
    def expire_at(self):
        from open_library.time.datetime import combine

        date = find_nth_weekday_of_month(self.year, self.month, calendar.THURSDAY, 2)

        dt = combine(date, Time(15, 45))

        return dt

    def to_dict(self):
        return self.__dict__

    @property
    def expire_at_str(self):
        date = self.expire_at

        return date.isoformat()

    @classmethod
    def get_derivative_type_from_code(cls, derivative_type_code):
        # Look for the corresponding DerivativeType
        for derivative_type, code in name_to_code_map.items():
            if code == derivative_type_code:
                return derivative_type
        # Handle the case where the code is not found
        raise ValueError(f"No matching DerivativeType for code {derivative_type_code}")

    @classmethod
    def get_derivative_code_from_type(cls, derivative_type):
        if derivative_type in name_to_code_map:
            return name_to_code_map[derivative_type]
        raise ValueError(f"No matching DerivativeTypeCode for code {derivative_type}")
