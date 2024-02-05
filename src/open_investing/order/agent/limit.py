#!/usr/bin/env python3
from open_investing.event_spec.event_spec import OrderEventSpec
from open_investing.task_spec.task_spec_handler_registry import TaskSpecHandlerRegistry

from open_library.locator.service_locator import ServiceKey

from open_investing.order.const.order import (
    OrderEventName,
    OrderCommandName,
    OrderPriceType,
    OrderSide,
    OrderType,
)
from typing import ClassVar
from open_investing.task_spec.order.order import OrderSpec, OrderAgent
import logging

logger = logging.getLogger(__name__)


class LimitOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = OrderType.Limit
    spec_type_name: str = spec_type_name_classvar


@TaskSpecHandlerRegistry.register_class
class LimitOrderAgent(OrderAgent):
    task_spec_cls = LimitOrderSpec

    order_type = OrderType.Limit
    order_price_type = OrderPriceType.Limit

    def __init__(self, order_spec):
        super().__init__(order_spec)

    async def on_order_command(self, order_info):
        order_spec = order_info["task_spec"]
        logger.info(f"on_order_command: {order_spec}")
        order_id = order_spec.order_id

        order_data_manager = self.order_data_manager
        exchange_manager = self.exchange_manager
        order = None
        if order_id:
            order = await order_data_manager.get_single_order(
                filter_params=dict(id=order_id)
            )
        if not order:
            order = await order_data_manager.prepare_order(
                params=dict(
                    id=order_id,
                    quantity_exposure=order_spec.quantity_exposure,
                    quantity_multiplier=order_spec.quantity_multiplier,
                    order_type=self.order_type,
                    security_code=order_spec.security_code,
                    strategy_session_id=order_spec.strategy_session_id,
                    side=order_spec.order_side,
                    parent_order_id=order_spec.parent_order_id,
                    order_price_type=self.order_price_type,
                    price_amount=order_spec.price.amount,
                    currency=order_spec.price.currency,
                    decision_id=order_spec.decision_id,
                )
            )

        command = order_info["command"]

        match command.name:
            case OrderCommandName.Open:
                order_event_broker = self.order_event_broker
                order_event_spec = OrderEventSpec(order_id=order_id)

                order_event_broker.subscribe(order_event_spec, self.enqueue_order_event)

                await self.order_service.open_order(order, exchange_manager)
            case OrderCommandName.CancelRemaining:
                await self.order_service.cancel_remaining_order(order, exchange_manager)

    async def on_order_event(self, order_info):
        event_spec = order_info["event_spec"]
        order = order_info["order"]
        data = order_info.get("data")

        logger.info(f"on_order_event: {event_spec}")

        event_name = event_spec.name

        match event_name:
            case OrderEventName.Filled:
                pass
                # check if filled,
            case _:
                pass

        pass
