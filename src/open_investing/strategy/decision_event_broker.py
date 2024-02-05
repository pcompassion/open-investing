#!/usr/bin/env python3

from typing import Any

from open_library.locator.service_locator import ServiceKey
from open_library.observe.pubsub_broker import PubsubBroker
from pydantic import BaseModel


class DecisionEventBroker(PubsubBroker):
    service_key = ServiceKey(
        service_type="pubsub_broker",
        service_name="decision_event_broker",
    )
