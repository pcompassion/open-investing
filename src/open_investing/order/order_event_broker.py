#!/usr/bin/env python3

from typing import Any

from open_investing.locator.service_locator import ServiceKey
from open_investing.order.const.order import OrderEventName
from open_library.observe.pubsub_broker import PubsubBroker
from pydantic import BaseModel


class OrderEvent(BaseModel):
    name: OrderEventName

    data: dict[str, Any] | None = None


class OrderEventBroker(PubsubBroker):
    service_key = ServiceKey(
        service_type="pubsub_broker",
        service_name="order_event_broker",
    )
