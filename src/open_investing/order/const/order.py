#!/usr/bin/env python3

from enum import Enum, auto


class OrderType(str, Enum):
    """
    type of orders that are supported
    """

    Market = "market"
    Limit = "limit"

    BestMarketIceberg = "best_market_iceberg"

    BestLimit = "best_limit"
    BestLimitLeg = "best_limit_leg"


SINGLE_ORDER_TYPES = (OrderType.Market, OrderType.Limit)


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderPriceType(Enum):
    Limit = "limit"
    Market = "market"


class OrderExchangeEventName(str, Enum):
    Filled = "filled"
    Cancelled = "cancelled"


class OrderCommandName(str, Enum):
    Open = "open"


class OrderOtherEventName(str, Enum):
    ExchangePlaceRequest = "exchange_place_request"
    ExchangePlaceSuccess = "exchange_place_success"
    ExchangePlaceFailure = "exchange_place_failure"


OrderEventName = Enum("OrderEventName", {**OrderExchangeEventName, **OrderCommandName})
