#!/usr/bin/env python3
from enum import Enum, auto


class MarketSecurityType(str, Enum):
    STOCK = "stock"
    DERIVATIVE = "derivative"
    UNDEFINED = "undefined"


class ApiType(str, Enum):
    Stock = "stock"
    Derivative = "derivative"

    Undefined = "undefined"


class MarketStatus(str, Enum):
    Undefined = "undefined"
    Open = "open"
    Closed = "closed"


class MarketType(str, Enum):
    Undefined = "undefined"
    FutureOptionDay = "future_option_day"
    FutureOptionNight = "future_option_night"
