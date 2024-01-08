#!/usr/bin/env python3
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


class MarketOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = "order.market_order"
    spec_type_name: str = spec_type_name_classvar


@TaskSpecHandlerRegistry.register_class
class MarketOrderAgent(OrderAgent):
    task_spec_cls = MarketOrderSpec

    order_type = OrderType.Market
    order_price_type = OrderPriceType.Market

    def __init__(self, order_spec):
        super().__init__(order_spec)

    async def on_order_command(self, order_info):
        order_spec = order_info["task_spec"]
        order_id = order_spec.order_id

        order_data_manager = self.order_data_manager
        exchange_manager = self.exchange_manager
        order = None
        if order_id:
            order = await order_data_manager.get(
                filter_params=dict(id=order_id, order_type=self.order_type)
            )
        if not order:
            order = await order_data_manager.prepare_order(
                params=dict(
                    quantity=order_spec.quantity,
                    order_type=self.order_type,
                    security_code=order_spec.security_code,
                    side=OrderSide.Buy,
                    parent_order_id=order_spec.parent_order_id,
                    order_price_type=self.order_price_type,
                )
            )

        command = order_info["command"]

        match command.name:
            case OrderCommandName.Open:
                order_event_broker = self.order_event_broker

                order_event_broker.subscribe(order.id, self.enqueue_order_event)

                await self.order_service.open_order(order, exchange_manager)
            case OrderCommandName.CancelRemaining:
                await self.order_service.cancel_remaining_order(order, exchange_manager)

    async def on_order_event(self, order_info):
        order_event = order_info["event"]
        logger.info(f"on_order_event: {order_event}")
        order = order_info["order"]

        event_name = order_event.name

        match event_name:
            case OrderEventName.Filled:

                # check if filled,
            case _:
                pass

        pass
