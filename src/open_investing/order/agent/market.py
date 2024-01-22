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
from open_investing.event_spec.event_spec import OrderEventSpec
from open_library.observe.listener_spec import ListenerSpec
from open_library.observe.const import ListenerType

logger = logging.getLogger(__name__)


class MarketOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = OrderType.Market
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
        logger.info(f"on_order_command: {order_spec.spec_type_name}")

        order_id = order_spec.order_id

        order_data_manager = self.order_data_manager
        exchange_manager = self.exchange_manager
        order_event_broker = self.order_event_broker
        order = None
        if order_id:
            order = await order_data_manager.get_single_order(
                filter_params=dict(id=order_id)
            )
        if not order:
            order = await order_data_manager.prepare_order(
                params=dict(
                    quantity=order_spec.quantity,
                    order_type=self.order_type,
                    security_code=order_spec.security_code,
                    side=order_spec.order_side,
                    parent_order_id=order_spec.parent_order_id,
                    order_price_type=self.order_price_type,
                    strategy_session_id=order_spec.strategy_session_id,
                    decision_id=order_spec.decision_id,
                    id=order_id,
                )
            )

        command = order_info["command"]

        match command.name:
            case OrderCommandName.Open:
                order_event_spec = OrderEventSpec(order_id=order_id)
                order_event_broker.subscribe(order_event_spec, self.enqueue_order_event)

                await self.order_service.open_order(order, exchange_manager)
            case OrderCommandName.CancelRemaining:
                await self.order_service.cancel_remaining_order(order, exchange_manager)

            case OrderCommandName.Close:
                # TODO maybe need to do something for market order as well

                offsetting_order = await order_data_manager.prepare_order(
                    params=dict(
                        quantity=order.filled_quantity,
                        order_type=self.order_type,
                        security_code=order_spec.security_code,
                        side=OrderSide(order.side).opposite,
                        parent_order_id=order_spec.parent_order_id,
                        order_price_type=self.order_price_type,
                    )
                )
                offsetted_order_id = order_spec.order_id
                offsetted_order = order
                assert offsetted_order_id == offsetted_order.id

                order_event_spec = OrderEventSpec(order_id=offsetted_order_id)
                order_event_broker.subscribe(order_event_spec, self.enqueue_order_event)

                await self.order_service.offset_order(
                    offsetting_order,
                    offsetted_order_id,
                    offset_quantity=offsetted_order.filled_quantity,
                    exchange_manager=exchange_manager,
                )

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
