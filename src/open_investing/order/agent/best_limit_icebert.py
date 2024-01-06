#!/usr/bin/env python3
import math
from open_investing.task_spec.task_spec_handler_registry import TaskSpecHandlerRegistry
from uuid import uuid4
from open_investing.task.task_command import SubCommand, TaskCommand
import logging
from open_investing.order.const.order import (
    OrderCommandName,
    OrderEventName,
    OrderSide,
    OrderType,
)
import asyncio
from open_investing.locator.service_locator import ServiceKey
from typing import ClassVar

from open_investing.order.models.order import Order
from open_investing.task_spec.order.order import (
    OrderAgent,
    OrderCommand,
    OrderSpec,
    OrderTaskCommand,
)


logger = logging.getLogger(__name__)


class BestLimitIcebergOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = "order.best_limit_iceberg"
    spec_type_name: str = spec_type_name_classvar

    max_tick: int


@TaskSpecHandlerRegistry.register_class
class BestLimitIcebergOrderAgent(OrderAgent):
    task_spec_cls = BestLimitIcebergOrderSpec

    order_type = OrderType.BestLimitIceberg

    """
    - 주문형태2-3. 지정가 주문 -최우선 지정가
    - 상황: 시급하지 않은 상황에서 최우선 호가로 market impact를 최소화하는 거래
    - 목표 수량만큼 주문하되 max-tick만큼 시장이 반대로 가는 경우 최우선 지정가로 갱신하면서 목표 수량을 채우는 매매
    ```python
    def 최우선_지정가(목표수량=N, max_tick=max_tick):
      총체결수량 =0
      while(총체결수량 < N):
        최우선지정가주문(n=N-총체결수량)
        wait until(abs(현재가-지정가) >max_tick*1tick가격 or 체결량>=n):
          총체결수량=총체결수량+체결량
        if 총체결수량 < N:
          pending중인 주문(n-체결량) 취소
        elif 총체결수량 >=N:
          return
    """

    def __init__(self, order_spec):
        super().__init__(order_spec)

        self.cancel_events = {}
        self.run_order_task = None

    async def run_order(self, order_spec, order, command_queue: asyncio.Queue):
        order_data_manager = self.order_data_manager
        order_event_broker = self.order_event_broker

        composite_order = order
        time_interval_second = order_spec.time_interval_second
        split = order_spec.split
        security_code = order_spec.security_code
        quantity = order_spec.quantity

        filled_quantity = order.filled_quantity

        orders = dict()

        while filled_quantity < quantity:
            if not command_queue.empty():
                command = await command_queue.get()
                if command == "STOP":
                    break

            remaining_quantity = quantity - filled_quantity
            quantity_partial = min(quantity / split, remaining_quantity)
            # TODO: stock seems to only allows integer
            quantity_partial = math.ceil(quantity_partial)
            if quantity_partial == 0:
                quantity_partial = remaining_quantity

            order_id = uuid4()
            orders[order_id] = None
            order_event_broker.subscribe(order_id, self.enqueue_order_event)

            order_spec_dict = self.base_spec_dict | {
                "spec_type_name": "order.limit_order",
                # "quantity": quantity_partial,
                # TODO: quantity type
                "quantity": int(quantity_partial),
                "order_id": order_id,
                "security_code": security_code,
            }

            command = OrderTaskCommand(
                name="command", order_command=OrderCommand(name=OrderCommandName.Open)
            )

            order_task_dispatcher = self.order_task_dispatcher
            await order_task_dispatcher.dispatch_task(order_spec_dict, command)

            await asyncio.sleep(time_interval_second)
            order = await order_data_manager.get(filter_params=dict(id=order_id))
            filled_quantity_new = order.filled_quantity

            if filled_quantity_new < quantity_partial:
                command = OrderTaskCommand(
                    name="command",
                    order_command=OrderCommand(name=OrderCommandName.Start),
                )

                cancel_event = asyncio.Event()

                self.cancel_events[order_id] = cancel_event

                remaining_quantity = quantity_partial - filled_quantity_new

                cancel_order_spec_dict = self.base_spec_dict | {
                    "spec_type_name": "order.cancel_remaining",
                    "cancel_quantity": remaining_quantity,
                    "order_id": order_id,
                    "security_code": security_code,
                }

                await order_task_dispatcher.dispatch_task(
                    cancel_order_spec_dict, command
                )

                try:
                    await asyncio.wait_for(cancel_event.wait(), timeout=10)
                except asyncio.TimeoutError:
                    logger.warning(f"cancel order timed out {order_id}")

    async def on_order_event(self, order_info):
        order_event = order_info["order_event"]
        logger.info(f"on_order_event: {order_event}")

        order = order_info["order"]

        event_name = order_event.name

        match event_name:
            case OrderEventName.Filled:
                # order is filled, do something
                pass

            case OrderEventName.CancelSuccess:
                order_id = order.id

                event = self.cancel_events.get(order_id)
                if event:
                    event.set()
                    del self.cancel_events[event]
            case _:
                pass

        pass

    async def on_order_command(self, order_info):
        order_spec = order_info["task_spec"]

        strategy_session_id = order_spec.strategy_session_id
        decision_id = order_spec.decision_id

        order_id = order_spec.order_id

        order_data_manager = self.order_data_manager
        order = None
        if order_id:
            order = await order_data_manager.get(
                filter_params=dict(id=order_id, order_type=self.order_type)
            )

        if order is None:
            order = await order_data_manager.prepare_order(
                params=dict(
                    id=order_id,
                    quantity=order_spec.quantity,
                    order_type=self.order_type,
                    strategy_session_id=strategy_session_id,
                    decision_id=decision_id,
                    data=dict(
                        security_code=order_spec.security_code,
                        side=OrderSide.Buy,
                        time_interval_second=order_spec.time_interval_second,
                        split=order_spec.split,
                    ),
                ),
                save=True,
            )

        command = order_info["command"]

        if command.name == OrderCommandName.Open:
            if self.run_order_task:
                logger.warning("already running order task")
                return

            command_queue = asyncio.Queue()
            self.run_order_task = asyncio.create_task(
                self.run_order(order_spec, order, command_queue)
            )

    async def get_market_price(self, security_code):
        price = None

        return price
