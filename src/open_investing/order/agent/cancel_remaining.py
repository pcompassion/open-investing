#!/usr/bin/env python3


from typing import ClassVar
from open_investing.task_spec.order.order import OrderAgent, OrderSpec
from open_investing.order.const.order import OrderCommandName, OrderEventName


class CancelRemainingOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = "order.cancel_remaining"
    spec_type_name: str = spec_type_name_classvar
    cancel_quantity: float


class CancelRemainingOrderAgent(OrderAgent):
    task_spec_cls = CancelRemainingOrderSpec

    def __init__(self, order_spec):
        super().__init__(order_spec)

    async def on_order_command(self, order_info):
        order_spec = order_info["task_spec"]
        order_id = order_spec.order_id

        order_data_manager = self.order_data_manager
        exchange_manager = self.exchange_manager

        order = await order_data_manager.get(filter_params=dict(id=order_id))

        command = order_info["command"]

        match command.name:
            case OrderCommandName.Start:  # this is actually start of cancel
                order_event_broker = self.order_event_broker

                cancel_quantity = order_spec.cancel_quantity

                order_event_broker.subscribe(order.id, self.enqueue_order_event)

                await self.order_service.cancel_order_quantity(
                    order, exchange_manager, cancel_quantity
                )

            case _:
                pass

    async def on_order_event(self, order_info):
        order_event = order_info["event"]
        order = order_info["order"]

        event_name = order_event.name

        match event_name:
            case OrderEventName.CancelSuccess:
                order_id = order.id
                # TODO: i need to shutdown myself

            case OrderEventName.ExchangeCancelFailure:
                # TODO: look at the reason
                # if remaining_quantity < cancel_quantity, then try with remaining_quantity
                pass
            case _:
                pass

        pass
