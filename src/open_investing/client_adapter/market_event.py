#!/usr/bin/env python3
from typing import Dict
from open_investing.market_event.market_event import MarketEvent

class MarketEventSourceRegistry:
    event_source_classes: Dict{MarketEvent, MarketEventSource} = {}

    @classmethod
    def register_class(cls, market_event: MarketEvent, target_cls):
        if market_event in cls.event_source_classes:
            raise Exception(f"MarketEvent {market_event} is already registered")

        cls.event_source_classes[market_event] = target_cls

    @classmethod
    def initialize_startup_classes(cls):
        for registered_cls in cls.startup_classes:
            obj = registered_cls()
            obj.init()
