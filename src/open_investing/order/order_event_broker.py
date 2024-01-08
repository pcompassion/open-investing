#!/usr/bin/env python3

from typing import Any

from open_library.locator.service_locator import ServiceKey
from open_investing.order.const.order import OrderEventName
from open_library.observe.pubsub_broker import PubsubBroker
from pydantic import BaseModel


class OrderEventBroker(PubsubBroker):
    service_keys = [
        ServiceKey(
            service_type="pubsub_broker",
            service_name="order_event_broker",
        ),
        ServiceKey(
            service_type="pubsub_broker",
            service_name="quote_event_broker",
        ),
    ]


# reuse as QuoteEventBroker
