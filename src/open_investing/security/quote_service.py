#!/usr/bin/env python3
from open_library.locator.service_locator import ServiceKey
import asyncio
from open_library.observe.subscription_manager import SubscriptionManager
from open_investing.event_spec.event_spec import EventSpec, QuoteEventSpec
from open_library.observe.listener_spec import ListenerSpec
from open_library.observe.const import ListenerType


class QuoteService:
    service_key = ServiceKey(
        service_type="service",
        service_name="quote_service",
    )

    def __init__(self):
        self.order_data_manager = None
        self.exchange_manager = None

        self.subscription_manager = SubscriptionManager()

    def set_exchange_manager(self, exchange_manager):
        self.exchange_manager = exchange_manager

    async def initialize(self):
        pass

    async def subscribe_quote(
        self, event_spec: QuoteEventSpec, listener_spec: ListenerSpec
    ):
        security_code = event_spec.security_code
        exchange_manager = self.exchange_manager

        listener_spec_me = ListenerSpec(
            service_key=self.service_key,
            listener_type=ListenerType.Callable,
            listener_or_name=self.on_quote_event,
        )

        if security_code:
            self.subscription_manager.subscribe(event_spec, listener_spec)
            exchange_manager.subscribe_quote(event_spec, listener_spec_me)

    async def on_quote_event(self, message):
        await self.subscription_manager.publish(message)
