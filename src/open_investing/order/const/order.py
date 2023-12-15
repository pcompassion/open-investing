#!/usr/bin/env python3

from enum import Enum, auto

class OrderType(Enum):
    '''
    type of orders that are supported
    '''

    Market = "market"
    Limit = "limit"

    BestLimitLeg = 'best_limit_leg'


class OrderDirection(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderPriceType(Enum):

    LIMIT = "limit"
    MARKET = "market"
