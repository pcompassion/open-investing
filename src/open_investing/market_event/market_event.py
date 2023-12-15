#!/usr/bin/env python3
from enum import Enum, auto
import functools
import operator
import itertools
from typing import Union, Dict


class MarketEventType(Enum):
    CANDLE = "candle"
    INDICATOR = "indicator"
    FUTURE_OPTION_CANDLE = "future_option_candle"


class MarketEventSourceType(Enum):
    EXCHANGE = "exchange"


class MarketEvent:

    """
    Represents a market event.
    currently,
    """

    def __init__(
        self,
        event_type: MarketEventType,
        source_name: str,
        cron_expression: str,
        data: Dict[str, Union[str, int, float]] = None,
        source_type: str = "exchange",
    ):
        self.event_type = event_type
        self.source_name = source_name
        self.source_type = source_type
        self.cron_expression = cron_expression
        self.data = data if data is not None else {}

    def __eq__(self, other):
        if isinstance(other, MarketEvent):
            return (
                self.event_type,
                self.source_name,
                self.cron_expression,
                tuple(self.data.items()),
            ) == (
                other.event_type,
                other.source_name,
                other.cron_expression,
                tuple(other.data.items()),
            )
        return NotImplemented

    def __hash__(self):
        # Hash the individual attributes
        attrs_hash = map(
            hash, (self.event_type, self.source_name, self.cron_expression)
        )

        # Hash the key-value pairs in the data dictionary
        data_items_hash = map(hash, tuple(self.data.items()))

        # Combine all hashes using XOR
        combined_hashes = itertools.chain(attrs_hash, data_items_hash)
        return functools.reduce(operator.xor, combined_hashes, 0)

    @property
    def source_manager(self):
        pass


class MarketEventSource:
    def __init__(self, market_event: MarketEvent):
        self.market_event = market_event
