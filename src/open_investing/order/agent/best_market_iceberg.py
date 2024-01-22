#!/usr/bin/env python3
from open_library.observe.const import ListenerType
from open_library.observe.listener_spec import ListenerSpec
from open_investing.event_spec.event_spec import OrderEventSpec
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
from open_library.locator.service_locator import ServiceKey
from typing import ClassVar

from open_investing.order.models.order import Order
from open_investing.task_spec.order.order import (
    OrderAgent,
    OrderCommand,
    OrderSpec,
    OrderTaskCommand,
)


logger = logging.getLogger(__name__)


class BestMarketIcebergOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = OrderType.BestMarketIceberg
    spec_type_name: str = spec_type_name_classvar

    time_interval_second: float
    split: int


@TaskSpecHandlerRegistry.register_class
class BestMarketIcebergOrderAgent(OrderAgent):
    task_spec_cls = BestMarketIcebergOrderSpec

    order_type = OrderType.BestMarketIceberg

    """
      - 주문형태2-2. 지정가 주문 -최유리 지정가
        - 상황: 어느 정도 시급한 상황이지만 market impact를 줄이면서 유리하게 매매하고 싶은 경우
        - 목표 수량(N)만 정해진 지정가
        - 목표수량의 1/k 만큼 t초 간격으로 최유리호가에 주문하되, 부분 체결되는    경우 남은 수량은 취소후 재 주문
        - 예) 목표 수량 100개(N=100)를 매수하는 경우, 총수량을 k개로 나눠서 market impact를 줄여서 체결시킴. 최유리호가에 10개씩 주문함. t초동안 체결되기를 기다린후, 전량 체결되는 경우는 다음 10개주문. 부분 체결 되는 경우 잔량은 취소후 다음 10개 주문. 반복하여 목표수량 N개가 모두 체결되기까지 반복


    def 최유리_지정가(목표수량=N, time_interval_second=t초, split=k):
      총체결수량=0
      while(총체결수량<N):
        체결량=0
        최유리지정가주문(n=min[N/k, N-총체결수량])
        wait(t초):
          총체결수량=총체결수량+체결량
        if 체결량<n:  #일부체결시
          pending중인 주문(n-체결량) 취소

        총체결수량=총체결수량+체결량


    """

    def __init__(self, order_spec):
        super().__init__(order_spec)

        self.cancel_events = {}
        self.run_order_task = None

    async def run_order(self, order_spec, order, command_queue: asyncio.Queue):
        try:
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

                order_event_spec = OrderEventSpec(order_id=order_id)
                listener_spec = ListenerSpec(
                    listener_type=ListenerType.Callable,
                    listener_or_name=self.enqueue_order_event,
                )

                order_event_broker.subscribe(order_event_spec, listener_spec)

                order_spec_dict = self.base_spec_dict | {
                    "spec_type_name": OrderType.Market,
                    # "quantity": quantity_partial,
                    # TODO: quantity type
                    "quantity": int(quantity_partial),
                    "order_id": order_id,
                    "security_code": security_code,
                }

                command = OrderTaskCommand(
                    name="command",
                    order_command=OrderCommand(name=OrderCommandName.Open),
                )

                order_task_dispatcher = self.order_task_dispatcher
                await order_task_dispatcher.dispatch_task(order_spec_dict, command)

                await asyncio.sleep(time_interval_second)
                order = await order_data_manager.get_single_order(
                    filter_params=dict(id=order_id)
                )
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
        except Exception as e:
            logger.exception(f"run_order: {e}")

    async def on_order_event(self, order_info):
        event_spec = order_info["event_spec"]
        order = order_info["order"]
        data = order_info.get("data")

        logger.info(f"on_order_event: {event_spec}")

        event_name = event_spec.name

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
                    side=order_spec.order_side,
                    data=dict(
                        security_code=order_spec.security_code,
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
