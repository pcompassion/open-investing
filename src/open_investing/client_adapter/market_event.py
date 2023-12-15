#!/usr/bin/env python3
from typing import Dict
from open_investing.market_event.market_event import MarketEventSpec, IMarketEventSource


class MarketEventSourceRegistry:
    event_source_classes: Dict[MarketEventSpec, IMarketEventSource] = {}

    @classmethod
    def register_class(cls, market_event_spec: MarketEventSpec, target_cls):
        if market_event_spec in cls.event_source_classes:
            raise Exception(
                f"MarketEventSpec {market_event_spec} is already registered"
            )

        cls.event_source_classes[market_event_spec] = target_cls

    @classmethod
    def initialize_startup_classes(cls):
        for registered_cls in cls.event_source_classes:
            obj = registered_cls()
            obj.init()
