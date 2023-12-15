#!/usr/bin/env python3
from pydantic import BaseModel
from typing import Dict, Union, Optional
from enum import Enum
import json
import functools
import operator
import itertools

from abc import ABC
from open_investing.const.const import EXCHANGE
from open_investing.store.store import store


class MarketEventType(Enum):
    CANDLE = "candle"
    INDICATOR = "indicator"
    FUTURE_OPTION_CANDLE = "future_option_candle"


class MarketEventSourceType(Enum):
    EXCHANGE = EXCHANGE


class MarketEventSpec(BaseModel):
    event_type: MarketEventType
    source_name: str
    cron_time: str
    data: Dict[str, Union[str, int, float]] = {}
    source_type: MarketEventSourceType = MarketEventSourceType.EXCHANGE

    def __str__(self):
        return f"{self.event_type.value} {self.source_type.value}:{self.source_name} {self.cron_time} {self.data}"

    def __str__(self):
        return f"{self.event_type.value} {self.source_type}:{self.source_name} {self.cron_time} {self.data}"

    def __eq__(self, other):
        if isinstance(other, MarketEventSpec):
            return (
                self.event_type,
                self.source_name,
                self.cron_time,
                tuple(self.data.items()),
            ) == (
                other.event_type,
                other.source_name,
                other.cron_time,
                tuple(other.data.items()),
            )
        return NotImplemented

    def __hash__(self):
        attrs_hash = map(hash, (self.event_type, self.source_name, self.cron_time))
        data_items_hash = map(hash, tuple(self.data.items()))
        combined_hashes = itertools.chain(attrs_hash, data_items_hash)
        return functools.reduce(operator.xor, combined_hashes, 0)

    @property
    def source_manager(self):
        if self.source_type == MarketEventSourceType.EXCHANGE:
            # Adjust this based on how 'store' and 'EXCHANGE' are defined.
            return store[EXCHANGE].get_exchange(
                self.source_name, event_type=self.event_type
            )


class IMarketEventSource(ABC):
    def __init__(self, market_event_spec: MarketEventSpec):
        self.market_event_spec = market_event_spec
