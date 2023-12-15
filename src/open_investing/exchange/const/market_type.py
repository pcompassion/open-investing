#!/usr/bin/env python3
from enum import Enum, auto

class MarketType(Enum):
    STOCK = "stock"
    DERIVATIVE = "derivative"
    UNDEFINED = "undefined"
