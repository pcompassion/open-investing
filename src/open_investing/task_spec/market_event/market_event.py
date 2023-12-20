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
from open_investing.app.task_app import app
from open_investing.exchange.const.market_type import ApiType


class MarketEventType(str, Enum):
    CANDLE = "candle"
    INDICATOR = "indicator"
    FUTURE_OPTION_CANDLE = "future_option_candle"


class MarketEventSourceType(str, Enum):
    EXCHANGE = EXCHANGE


class MarketEventSpec(TaskSpec):
    event_type: MarketEventType
    source_name: str
    source_type: MarketEventSourceType = MarketEventSourceType.EXCHANGE
    api_type: ApiType = ApiType.Stock

    def __str__(self):
        return f"{self.event_type} {self.source_type}:{self.source_name} {self.cron_time} {self.data}"

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

            return app.exchange_store.get_exchange(
                self.source_name, exchange_params=self.get_exchange_params()
            )

    def get_exchange_params(self):
        return dict(api_type=self.api_type)


class IMarketEventSource(TaskSpecHandler):
    def __init__(self, task_spec: MarketEventSpec):
        super().__init__(task_spec)  # market_event_spec is a TaskSpec

    @property
    def market_event_spec(self):
        return self.task_spec  # convenient
