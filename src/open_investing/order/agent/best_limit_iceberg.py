#!/usr/bin/env python3
from decimal import Decimal
from dataclasses import dataclass
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
from open_library.logging.logging_filter import IntervalLoggingFilter

logger = logging.getLogger(__name__)

quote_logger = logging.getLogger("quote")
interval_filter = IntervalLoggingFilter(60)  # Log once every 60 seconds
quote_logger.addFilter(interval_filter)


class BestLimitIcebergOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = OrderType.BestLimitIceberg
    spec_type_name: str = spec_type_name_classvar

    max_tick_diff: int
    tick_size: Decimal


@dataclass
class InternalOrderCommand:
    name: str
    data: any = None


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
        self.close_order_task = None

        self.tasks["run_quote_event"] = Task("run_quote_event", self.run_quote_event())

        self.quote_tracker = TimeDataTracker(time_window_seconds=10)
        self.order_fill_tracker = TimeDataTracker(time_window_seconds=10)

        self.quote = None
        self.composite_order = None
        self.filled_quantity = None
        self.order_command_queues = dict()
        self.limit_order_id = None

    async def run_order(self, order_spec, order):
        try:
            order_data_manager = self.order_data_manager
            order_event_broker = self.order_event_broker
            order_task_dispatcher = self.order_task_dispatcher

            self.composite_order = order
            max_tick_diff = order_spec.max_tick_diff
            security_code = order_spec.security_code
            quantity = order_spec.quantity

            self.filled_quantity = order.filled_quantity

            orders = dict()
            composite_order_id = order.id
            order_event_spec = None
            listener_spec = None
            order_side = order_spec.order_side

            order_command_queue = self.order_command_queues.get(composite_order_id)

            while self.filled_quantity < quantity:
                # TODO: probably need tighter check
                remaining_quantity = quantity - self.filled_quantity

                if order_command_queue is not None and not order_command_queue.empty():
                    internal_order_command = await order_command_queue.get()
                    name = internal_order_command.name

                    if name == "STOP" and self.limit_order_id:
                        await self.cancel_remaining(
                            self.limit_order_id, security_code, remaining_quantity
                        )

                        break

                try:
                    timed_data = await self.quote_tracker.wait_for_valid_data()
                    recent_quote = timed_data.data

                    if order_side == OrderSide.Buy:
                        price = recent_quote.bid_price_1
                    else:
                        price = recent_quote.ask_price_1

                    test = False

                    if test:
                        # for faster testing
                        if order_side == OrderSide.Buy:
                            # logger.info(
                            #     f"buying at {recent_quote.ask_price_2}, instead of {price}"
                            # )
                            price = recent_quote.ask_price_2
                        else:
                            # logger.info(
                            #     f"selling at {recent_quote.bid_price_2}, instead of {price}"
                            # )

                            price = recent_quote.bid_price_2

                except TimeoutError as e:
                    logger.warning(f"wait for quote data timeout {e}")
                    await self._subscribe_quote(order_spec.security_code)

                    continue

                    # shouldn't happen

                if self.quote is not None:
                    if order_side == OrderSide.Buy:
                        price_diff = price - self.quote.bid_price_1
                    else:
                        price_diff = self.quote.ask_price_1 - price

                    tick_diff = math.floor(price_diff.amount / order_spec.tick_size)

                    if tick_diff > max_tick_diff:
                        # TODO: cancel all
                        logger.info(
                            f"tick diff bigger than max_tick_diff {max_tick_diff}"
                        )
                        self.quote = recent_quote
                        await self.cancel_remaining(
                            self.limit_order_id,
                            security_code,
                            remaining_quantity,
                        )
                        continue
                    else:
                        # wait for fill
                        if self.limit_order_id:
                            try:
                                timed_data = (
                                    await self.order_fill_tracker.wait_for_valid_data(
                                        timeout_seconds=3
                                    )
                                )
                                continue
                            except TimeoutError as e:
                                logger.info(
                                    f"wait for order fill data timeout {self.limit_order_id}, tick_diff: {tick_diff}"
                                )
                                continue

                else:
                    self.quote = recent_quote

                order_id = self.limit_order_id = uuid4()
                orders[order_id] = None

                order_event_spec = OrderEventSpec(order_id=order_id)
                listener_spec = ListenerSpec(
                    listener_type=ListenerType.Callable,
                    listener_or_name=self.enqueue_order_event,
                )

                self.order_event_broker.subscribe(order_event_spec, listener_spec)

                order_spec_dict = self.base_spec_dict | {
                    "spec_type_name": OrderType.Limit,
                    # "quantity": quantity_partial,
                    # TODO: quantity type
                    "order_side": order_spec.order_side,
                    "quantity": int(remaining_quantity),
                    "order_id": order_id,
                    "parent_order_id": self.composite_order.id,
                    "strategy_session_id": order_spec.strategy_session_id,  # TODO: shouldnt be neccessary
                    "security_code": security_code,
                    "price": price,
                }

                command = OrderTaskCommand(
                    name="command",
                    order_command=OrderCommand(name=OrderCommandName.Open),
                )

                order_task_dispatcher = self.order_task_dispatcher
                await order_task_dispatcher.dispatch_task(order_spec_dict, command)

        except Exception as e:
            logger.exception(f"run_order: {e}")

    async def cancel_remaining(self, order_id, security_code, cancel_quantity):
        order_task_dispatcher = self.order_task_dispatcher

        command = OrderTaskCommand(
            name="command",
            order_command=OrderCommand(name=OrderCommandName.Start),
        )

        cancel_event = asyncio.Event()

        self.cancel_events[order_id] = cancel_event

        cancel_order_spec_dict = self.base_spec_dict | {
            "spec_type_name": "order.cancel_remaining",
            "cancel_quantity": cancel_quantity,
            "order_id": order_id,
            "security_code": security_code,
        }

        await order_task_dispatcher.dispatch_task(cancel_order_spec_dict, command)

        order_event_spec = OrderEventSpec(order_id=order_id)
        listener_spec = ListenerSpec(
            listener_type=ListenerType.Callable,
            listener_or_name=self.enqueue_order_event,
        )

        try:
            await asyncio.wait_for(cancel_event.wait(), timeout=10)
            self.order_event_broker.unsubscribe(order_event_spec, listener_spec)

        except asyncio.TimeoutError:
            logger.warning(f"cancel order timed out {order_id}")

    async def on_order_event(self, order_info):
        order_event_spec = order_info["event_spec"]
        logger.info(f"on_order_event: {order_event_spec}")

        order = order_info["order"]
        data = order_info["data"]

        event_name = order_event_spec.name

        match event_name:
            case OrderEventName.Filled:
                # order is filled, do something

                composite_order = await self.order_data_manager.get_composite_order(
                    filter_params=dict(id=self.composite_order.id)
                )
                self.filled_quantity = composite_order.filled_quantity

                date_at = data["date_at"]
                await self.order_fill_tracker.add_data(data, date_at)

            case OrderEventName.CancelSuccess:
                order_id = order.id

                event = self.cancel_events.get(order_id)
                self.limit_order_id = None
                if event:
                    event.set()
                    del self.cancel_events[event]
            case _:
                pass

        pass

    async def _subscribe_quote(self, security_code: str):
        quote_event_spec = QuoteEventSpec(security_code=security_code)
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

    async def on_order_command(self, order_info):
        order_spec = order_info["task_spec"]

        logger.info(f"on_command_event: {order_spec.spec_type_name}")

        strategy_session_id = order_spec.strategy_session_id
        decision_id = order_spec.decision_id

        order_id = order_spec.order_id

        order_data_manager = self.order_data_manager

        command = order_info["command"]

        await self._subscribe_quote(order_spec.security_code)

        match command.name:
            case OrderCommandName.Open:
                order = None
                if order_id:
                    order = await order_data_manager.get_composite_order(
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
                                max_tick_diff=order_spec.max_tick_diff,
                                tick_size=order_spec.tick_size,
                            ),
                        ),
                        save=True,
                    )

                if self.run_order_task:
                    logger.warning("already running order task")
                    return

                self.order_command_queues[order.id] = asyncio.Queue()

                self.run_order_task = asyncio.create_task(
                    self.run_order(order_spec, order)
                )

            case OrderCommandName.Close:
                order_command_queue = self.order_command_queues.get(order_spec.order_id)

                if order_command_queue:
                    internal_order_command = InternalOrderCommand(name="STOP")
                    await order_command_queue.put(internal_order_command)

                self.close_order_task = asyncio.create_task(
                    self.run_order(order_spec, order)
                )

    async def on_quote_event(self, event_info):
        event_spec = event_info["event_spec"]
        quote_logger.info(f"on_quote_event: {event_spec}")

        # price = event.data.get('price')

        quote_tracker = self.quote_tracker
        data = event_info["data"]

        date_at = data.date_at

        await quote_tracker.add_data(data, date_at)
