#!/usr/bin/env python3
from typing import Any
from open_library.base_spec.base_spec import BaseSpec
from open_investing.order.const.order import OrderEventName

from open_investing.const.code_name import SecurityType


class EventSpec(BaseSpec):
    def attr_names(self):
        # data is used as event data result
        names = self.model_dump(exclude_unset=True, exclude=set(("data"))).keys()

        return names


class QuoteEventSpec(EventSpec):
    spec_type_name: str = "quote"

    security_code: str | None = None
    security_type: SecurityType | list[SecurityType] | None = None

    @property
    def hash_keys(self):
        return ["spec_type_name", "security_code", "security_type"]


class OrderEventSpec(EventSpec):
    spec_type_name: str = "order"

    order_id: str
    name: OrderEventName

    data: dict[str, Any] | None = None
