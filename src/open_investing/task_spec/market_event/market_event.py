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

from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler

from open_investing.exchange.const.market_type import ApiType


class MarketEventType(str, Enum):
    CANDLE = "candle"
    INDICATOR = "indicator"
    FUTURE_OPTION_CANDLE = "future_option_candle"


class MarketEventSourceType(str, Enum):
    EXCHANGE = EXCHANGE


class MarketEventSpec(TaskSpec):
    event_type: MarketEventType
    # source_name: str
    # source_type: MarketEventSourceType = MarketEventSourceType.EXCHANGE

    def __str__(self):
        return f"{self.event_type} : {self.cron_time} {self.data}"

    def __eq__(self, other):
        if isinstance(other, MarketEventSpec):
            return (
                self.event_type,
                self.cron_time,
                tuple(self.data.items()),
            ) == (
                other.event_type,
                other.cron_time,
                tuple(other.data.items()),
            )
        return NotImplemented

    def __hash__(self):
        attrs_hash = map(hash, (self.event_type, self.cron_time))
        data_items_hash = map(hash, tuple(sorted(self.data.items())))
        combined_hashes = itertools.chain(attrs_hash, data_items_hash)
        return functools.reduce(operator.xor, combined_hashes, 0)


class IMarketEventSource(TaskSpecHandler):
    def __init__(self, task_spec: MarketEventSpec):
        super().__init__(task_spec)  # market_event_spec is a TaskSpec

    @property
    def market_event_spec(self):
        return self.task_spec  # convenient
