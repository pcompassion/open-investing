#!/usr/bin/env python3

from open_library.observe.pubsub_broker import PubsubBroker

from open_investing.order.const.order import OrderExchangeEventName


class OrderExchangeEvent(BaseModel):
    name: OrderExchangeEventName

    data: dict[str, Any] | None = None


class OrderExchangeEventBroker(PubsubBroker):
    service_key = ServiceKey(
        service_type="pubsub_broker",
        service_name="order_exchange_event_broker",
    )
