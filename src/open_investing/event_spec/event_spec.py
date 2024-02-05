#!/usr/bin/env python3
from typing import Any
from open_library.base_spec.base_spec import BaseSpec
from open_investing.order.const.order import OrderEventName
from uuid import UUID

from open_investing.const.code_name import DerivativeType
from open_investing.strategy.const.decision import DecisionEventName


class EventSpec(BaseSpec):
    pass
    # def attr_names(self):
    #     # data is used as event data result
    #     names = self.model_dump(
    #         exclude_none=True, exclude=set(["data", "service_keys"])
    #     ).keys()

    #     return names


class QuoteEventSpec(EventSpec):
    spec_type_name: str = "quote_event"

    security_code: str | None = None
    derivative_type: DerivativeType | list[DerivativeType] | None = None

    @property
    def hash_keys(self):
        return ["spec_type_name", "security_code", "derivative_type"]


class OrderEventSpec(EventSpec):
    spec_type_name: str = "order_event"

    order_id: UUID | None = None
    name: OrderEventName | None = None

    data: dict[str, Any] | None = None

    @property
    def hash_keys(self):
        return ["spec_type_name", "order_id"]


class DecisionEventSpec(EventSpec):
    spec_type_name: str = "decision_event"

    order_id: UUID | None = None
    name: DecisionEventName | None = None

    data: dict[str, Any] | None = None

    @property
    def hash_keys(self):
        return ["spec_type_name", "decision_id"]
