#!/usr/bin/env python3
from open_library.observe.listener_spec import ListenerSpec
from open_investing.event_spec.event_spec import OrderEventSpec, QuoteEventSpec
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
from open_investing.task.task import Task
from open_investing.event_spec.event_spec import EventSpec, QuoteEventSpec
from open_library.observe.listener_spec import ListenerSpec
from open_library.observe.const import ListenerType

from open_library.time_tracker.time_data_tracker import TimeDataTracker

logger = logging.getLogger(__name__)


class BestLimitIcebergOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = "order.best_limit_iceberg"
    spec_type_name: str = spec_type_name_classvar

    max_tick_diff: int
    tick_size: float


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

        self.tasks["run_quote_event"] = Task("run_quote_event", self.run_quote_event())

        self.time_data_tracker = TimeDataTracker(time_window_seconds=10)
        self.quote = None
        self.composite_order = None
        self.filled_quantity = None

    async def run_order(self, order_spec, order, command_queue: asyncio.Queue):
        order_data_manager = self.order_data_manager
        order_event_broker = self.order_event_broker

        self.composite_order = order
        max_tick_diff = order_spec.max_tick_diff
        security_code = order_spec.security_code
        quantity = order_spec.quantity

        self.filled_quantity = order.filled_quantity

        orders = dict()
        order_id = None
        order_event_spec = None
        listener_spec = None

        while self.filled_quantity < quantity:
            if not command_queue.empty():
                command = await command_queue.get()
                if command == "STOP":
                    break

            try:
                recent_quote = await self.time_data_tracker.wait_for_valid_data()
                price = recent_quote.bid_price_1
            except TimeoutError as e:
                print(e)
                raise e
                # shouldn't happen

            remaining_quantity = quantity - self.filled_quantity

            if self.quote is not None:
                price_diff = price - self.quote.bid_price_1

                tick_diff = math.floor(price_diff / order_spec.tick_size)

                if tick_diff > max_tick_diff:
                    self.quote = recent_quote

                    command = OrderTaskCommand(
                        name="command",
                        order_command=OrderCommand(name=OrderCommandName.Start),
                    )

                    cancel_event = asyncio.Event()

                    self.cancel_events[order_id] = cancel_event

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
                        self.order_event_broker.unsubscribe(
                            order_event_spec, listener_spec
                        )

                    except asyncio.TimeoutError:
                        logger.warning(f"cancel order timed out {order_id}")

            remaining_quantity = quantity - self.filled_quantity

            order_id = uuid4()
            orders[order_id] = None

            order_event_spec = OrderEventSpec(order_id=order_id)
            listener_spec = ListenerSpec(
                listener_type=ListenerType.Callable,
                listener_or_name=self.enqueue_order_event,
            )

            self.order_event_broker.subscribe(order_event_spec, listener_spec)

            order_spec_dict = self.base_spec_dict | {
                "spec_type_name": "order.limit_order",
                # "quantity": quantity_partial,
                # TODO: quantity type
                "quantity": int(remaining_quantity),
                "order_id": order_id,
                "security_code": security_code,
                "price": price,
            }

            command = OrderTaskCommand(
                name="command", order_command=OrderCommand(name=OrderCommandName.Open)
            )

            order_task_dispatcher = self.order_task_dispatcher
            await order_task_dispatcher.dispatch_task(order_spec_dict, command)

    async def on_order_event(self, order_info):
        order_event_spec = order_info["event_spec"]
        logger.info(f"on_order_event: {order_event_spec}")

        order = order_info["order"]

        event_name = order_event_spec.name

        match event_name:
            case OrderEventName.Filled:
                # order is filled, do something

                order = await order_data_manager.get(
                    filter_params=dict(id=self.composite_order.id)
                )
                self.filled_quantity = order.filled_quantity

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
                        max_tick_diff=order_spec.max_tick_diff,
                        tick_size=order_spec.tick_size,
                    ),
                ),
                save=True,
            )

        command = order_info["command"]

        if command.name == OrderCommandName.Open:
            if self.run_order_task:
                logger.warning("already running order task")
                return

            quote_event_spec = QuoteEventSpec(security_code=order_spec.security_code)
            listener_spec = ListenerSpec(
                listener_type=ListenerType.Callable,
                listener_or_name=self.enqueue_quote_event,
            )

            self.quote_event_broker.subscribe(quote_event_spec, listener_spec)

            listener_spec = ListenerSpec(
                service_key=ServiceKey(
                    service_type="pubsub_broker",
                    service_name="quote_event_broker",
                ),
                listener_type=ListenerType.Service,
                listener_or_name="enqueue_message",
            )

            await self.quote_service.subscribe_quote(quote_event_spec, listener_spec)

            command_queue = asyncio.Queue()
            self.run_order_task = asyncio.create_task(
                self.run_order(order_spec, order, command_queue)
            )

    async def on_quote_event(self, event_info):
        event = event_info["event"]
        logger.info(f"on_quote_event: {event}")

        # price = event.data.get('price')

        time_data_tracker = self.time_data_tracker
        data = event.data

        date_at = data["date_at"]

        time_data_tracker.add_data(event.data, date_at)
