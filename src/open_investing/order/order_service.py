#!/usr/bin/env python3

from open_library.observe.pubsub_broker import PubsubBroker
from open_investing.event_spec.event_spec import OrderEventSpec

from open_library.locator.service_locator import ServiceKey
import asyncio

from open_library.time.datetime import now_local
from open_investing.order.const.order import OrderEventName
from open_library.observe.subscription_manager import SubscriptionManager
from open_investing.event_spec.event_spec import OrderEventSpec
from open_library.observe.listener_spec import ListenerSpec
from open_library.observe.const import ListenerType
import logging

logger = logging.getLogger(__name__)


class OrderService:
    # https://chat.openai.com/c/ae7e132e-9005-441c-b0a1-6490b31cb938
    """
    Flow: OrderService does Orchestration

    request: service -> api_manager
    order execution response: api_manager -> pubsub -> service
    service does bookeeping: handle_filled_event
    after bookeeping, send event about update

    """

    service_key = ServiceKey(
        service_type="service",
        service_name="order_service",
    )

    def __init__(self):
        self.order_data_manager = None
        self.api_manager = None
        self.order_event_broker = None
        self.order_event_queue = asyncio.Queue()
        self.order_event_task = None
        self.exchange_manager = None
        self.running_tasks = set()

    async def initialize(self):
        self.order_event_task = asyncio.create_task(self.run_order_event())

    def set_order_data_manager(self, order_data_manager):
        self.order_data_manager = order_data_manager

    def set_order_event_broker(self, order_event_broker: PubsubBroker):
        self.order_event_broker = order_event_broker

    def set_exchange_manager(self, exchange_manager):
        self.exchange_manager = exchange_manager

    async def on_order_event(self, order_info):
        order_data_manager = self.order_data_manager
        order_event_broker = self.order_event_broker

        event_spec = order_info["event_spec"]
        order = order_info["order"]
        data_initial = order_info.get("data")

        event_name = event_spec.name

        match event_name:
            case OrderEventName.ExchangeFilled:
                filled_data = await order_data_manager.handle_filled_event(
                    data_initial, order=order
                )

                data = data_initial | filled_data
                order_event_spec = OrderEventSpec(
                    order_id=order.id,
                    name=OrderEventName.Filled,
                )

                message = dict(
                    event_spec=order_event_spec,
                    order=order,
                    data=data,
                )

                await order_event_broker.enqueue_message(message)

                # check if filled,
            case _:
                pass

        pass

    async def enqueue_order_event(self, order_event):
        await self.order_event_queue.put(order_event)

    async def run_order_event(self):
        while True:
            try:
                order_event = await self.order_event_queue.get()

                await self.on_order_event(order_event)
            except Exception as e:
                logger.exception(f"run_order_event: {e}")

    async def _open_order(self, order, exchange_manager):
        order_data_manager = self.order_data_manager
        exchange_manager = self.exchange_manager
        order_event_broker = self.order_event_broker

        await order_data_manager.record_event(
            event_params=dict(
                event_name=OrderEventName.ExchangeOpenRequest,
                date_at=now_local(),
            ),
            order=order,
        )

        order_event_spec = OrderEventSpec(order_id=order.id)
        listener_spec = ListenerSpec(
            listener_type=ListenerType.Callable,
            listener_or_name=self.enqueue_order_event,
        )

        order_event_broker.subscribe(order_event_spec, listener_spec)  # type: ignore

        exchange_order_id, _ = await exchange_manager.open_order(order)

        await order_data_manager.save(
            order, save_params=dict(exchange_order_id=exchange_order_id)
        )
        pass

    async def open_order(self, order, exchange_manager):
        logger.info(f"open_order: {order.id} {order.order_type}")
        task = asyncio.create_task(self._open_order(order, exchange_manager))

        self.running_tasks.add(task)
        task.add_done_callback(lambda t: self.running_tasks.remove(t))

    async def offset_order(
        self, offsetting_order, offsetted_order_id, offset_quantity, exchange_manager
    ):
        task = asyncio.create_task(
            self._offset_order(
                offsetting_order, offsetted_order_id, offset_quantity, exchange_manager
            )
        )

        self.running_tasks.add(task)
        task.add_done_callback(lambda t: self.running_tasks.remove(t))

    async def _offset_order(
        self, offsetting_order, offsetted_order_id, offset_quantity, exchange_manager
    ):
        # TODO: maybe do something other than open_order
        order_data_manager = self.order_data_manager

        await order_data_manager.create_offset_order_relation(
            offsetting_order=offsetting_order,
            offsetted_order_id=offsetted_order_id,
            offset_quantity=offset_quantity,
        )

        return await self._open_order(offsetting_order, exchange_manager)

    async def _cancel_order_quantity(self, order, exchange_manager, cancel_quantity):
        order_data_manager = self.order_data_manager
        exchange_manager = self.exchange_manager
        order_event_broker = self.order_event_broker

        await order_data_manager.record_event(
            event_params=dict(
                event_name=OrderEventName.ExchangeCancelRequest,
                date_at=now_local(),
                cancel_quantity=cancel_quantity,
            ),
            order=order,
        )

        order_event_broker.subscribe(order.id, self.enqueue_order_event)  # type: ignore

        cancel_order_result, _ = await exchange_manager.cancel_order_quantity(
            order, cancel_quantity
        )

        cancelled_quantity = cancel_order_result["cancelled_quantity"]

        event_name = OrderEventName.ExchangeCancelFailure
        next_event_name = OrderEventName.CancelFailure
        if cancelled_quantity > 0:
            event_name = OrderEventName.ExchangeCancelSuccess
            next_event_name = OrderEventName.CancelSuccess

        event_params = dict(
            event_name=event_name, date_at=now_local(), **cancel_order_result
        )
        await order_data_manager.record_event(
            event_params=event_params,
            order=order,
        )

        order_event_spec = OrderEventSpec(
            order_id=order.id,
            name=next_event_name,
        )
        data = event_params
        message = dict(
            event_spec=order_event_spec,
            order=order,
            data=data,
        )

        await order_event_broker.enqueue_message(message)

    async def cancel_order_quantity(self, order, exchange_manager, cancel_quantity):
        task = asyncio.create_task(
            self._cancel_order_quantity(order, exchange_manager, cancel_quantity)
        )

        self.running_tasks.add(task)
        task.add_done_callback(lambda t: self.running_tasks.remove(t))
