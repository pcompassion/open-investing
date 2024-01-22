#!/usr/bin/env python3

from typing import Any

from open_library.locator.service_locator import ServiceKey
from open_investing.order.const.order import OrderEventName
from open_library.observe.pubsub_broker import PubsubBroker
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class OrderEventBroker(PubsubBroker):
    service_key = ServiceKey(
        service_type="pubsub_broker",
        service_name="order_event_broker",
    )

    async def run(self):
        self.running = True
        while self.running:
            try:
                message = await self.queue.get()
                await self.subscription_manager.publish(message)
                # rate limiting

            except Exception as e:
                logger.exception(f"order event broker run: {e}")


# reuse as QuoteEventBroker
