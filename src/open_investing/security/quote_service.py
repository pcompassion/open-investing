#!/usr/bin/env python3
from open_library.locator.service_locator import ServiceKey
import asyncio
from open_library.observe.subscription_manager import SubscriptionManager
from open_investing.event_spec.event_spec import EventSpec, QuoteEventSpec
from open_library.observe.listener_spec import ListenerSpec
from open_library.observe.const import ListenerType
from open_library.asynch.queue import DroppingQueue
import logging

logger = logging.getLogger(__name__)


class QuoteService:
    service_key = ServiceKey(
        service_type="service",
        service_name="quote_service",
    )

    def __init__(self):
        self.order_data_manager = None
        self.exchange_manager = None

        self.subscription_manager = SubscriptionManager()
        self.queue = DroppingQueue(maxsize=1000)
        self.running = False
        self.run_task = None

    def set_exchange_manager(self, exchange_manager):
        self.exchange_manager = exchange_manager

    async def initialize(self):
        self.run_task = asyncio.create_task(self.run())

    async def subscribe_quote(
        self, event_spec: QuoteEventSpec, listener_spec: ListenerSpec
    ):
        # return
        security_code = event_spec.security_code
        exchange_manager = self.exchange_manager

        listener_spec_me = ListenerSpec(
            service_key=self.service_key,
            listener_type=ListenerType.Callable,
            listener_or_name=self.enqueue_message,
        )

        if security_code:
            self.subscription_manager.subscribe(event_spec, listener_spec)
            await exchange_manager.subscribe_quote(event_spec, listener_spec_me)

    async def enqueue_message(self, message):
        await self.queue.put(message)

    async def run(self):
        self.running = True
        while self.running:
            try:
                message = await self.queue.get()
                logger.info(f"publishing quote")
                await self.subscription_manager.publish(message)
                # rate limiting
                await asyncio.sleep(1)
            except Exception as e:
                logger.exception(f"quote service run: {e}")

    def stop_processing(self):
        self.running = False
