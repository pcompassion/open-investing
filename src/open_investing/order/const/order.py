#!/usr/bin/env python3

from enum import Enum, auto


class OrderType(str, Enum):
    """
    type of orders that are supported
    """

    Market = "market"
    Limit = "limit"

    BestMarketIceberg = "best_market_iceberg"
    BestLimitIceberg = "best_limit_iceberg"


SINGLE_ORDER_TYPES = (OrderType.Market, OrderType.Limit)


class OrderSide(str, Enum):
    Buy = "buy"
    Sell = "sell"


class OrderPriceType(str, Enum):
    Limit = "limit"
    Market = "market"


class OrderCommandName(str, Enum):
    Open = "open"
    Cancel = "cancel"
    CancelRemaining = "cancel_remaining"
    Close = "close"

    Start = "start"


class OrderEventName(str, Enum):
    ExchangeOpenRequest = "exchange.open_request"  # place request
    ExchangeOpenSuccess = "exchange.open_success"  # place success
    ExchangeOpenFailure = "exchange.open_failure"

    ExchangeCancelRequest = "exchange.cancel_request"  # cancel request
    ExchangeCancelSuccess = "exchange.cancel_success"  # cancel success
    ExchangeCancelFailure = "exchange.cancel_failure"

    ExchangeFilled = "exchange.filled"  # exchange notification for fill
    ExchangeCancelled = "exchange.cancelled"  # exchange notification for cancel

    Filled = "filled"  # order fill is recorded in db
    CancelSuccess = "cancel_success"  # order cancel is recorded in db
    CancelFailure = "cancel_failure"  # order cancel is recorded in db
