#!/usr/bin/env python3

from enum import Enum, auto


class OrderType(str, Enum):
    """
    type of orders that are supported
    """

    Market = "market"
    Limit = "limit"

    BestMarket = "best_market"
    BestLimit = "best_limit"
    BestLimitLeg = "best_limit_leg"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderPriceType(Enum):
    Limit = "limit"
    Market = "market"
