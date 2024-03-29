#!/usr/bin/env python3

from enum import Enum, auto


class OrderType(str, Enum):
    """
    type of orders that are supported
    """

    Market = "order.market"
    Limit = "order.limit"

    BestMarketIceberg = "order.best_market_iceberg"
    BestLimitIceberg = "order.best_limit_iceberg"

    @property
    def is_single_order(self):
        return self in [OrderType.Market, OrderType.Limit]


SINGLE_ORDER_TYPES = (OrderType.Market, OrderType.Limit)


class OrderSide(str, Enum):
    Buy = "buy"
    Sell = "sell"
    Undefined = "undefined"

    @property
    def opposite(self):
        if self == OrderSide.Buy:
            return OrderSide.Sell
        elif self == OrderSide.Sell:
            return OrderSide.Buy
        else:
            raise ValueError("Invalid OrderSide")


class OrderPriceType(str, Enum):
    Limit = "limit"
    Market = "market"


class OrderCommandName(str, Enum):
    Open = "open"
    Cancel = "cancel"
    CancelRemaining = "cancel_remaining"
    Close = "close"

    Offset = "offset"

    Start = "start"


class OrderEventName(str, Enum):
    ExchangeOpenRequest = "exchange.open_request"  # place request
    ExchangeOpenSuccess = "exchange.open_success"  # place success
    ExchangeOpenFailure = "exchange.open_failure"
    ExchangeOpenFailureNonRecoverable = "exchange.open_failure.non_recoverable"

    ExchangeCancelRequest = "exchange.cancel_request"  # cancel request
    ExchangeCancelSuccess = "exchange.cancel_success"  # cancel success
    ExchangeCancelFailure = "exchange.cancel_failure"

    ExchangeFilled = "exchange.filled"  # exchange notification for fill
    ExchangeCancelled = "exchange.cancelled"  # exchange notification for cancel

    Filled = "filled"  # order fill is recorded in db
    FullyOffsetted = "fully_offsetted"
    CancelSuccess = "cancel_success"  # order cancel is recorded in db
    CancelFailure = "cancel_failure"  # order cancel is recorded in db


class OrderCloseReason(str, Enum):
    TakeProfit = "take_profit"
    StopLoss = "stop_loss"
    Manual = "manual"


class OrderLifeStage(str, Enum):
    Undefined = "undefined"

    ExchangeOpenRequest = "exchange_open_request"
    ExchangeOpenSuccess = "exchange.open_success"  # place success
    ExchangeOpenFailure = "exchange.open_failure"

    Opened = "opened"  # there's some filled quantity
    Fullfilled = "fullfilled"

    FullyOffsetted = "fully_offsetted"
    Closed = "closed"
