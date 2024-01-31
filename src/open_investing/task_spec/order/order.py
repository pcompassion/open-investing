#!/usr/bin/env python3

from decimal import Decimal
from open_investing.price.money import Money
import operator
import functools
from uuid import UUID
from open_investing.task.task import Task
import asyncio
from typing import ClassVar, Type, cast
from typing import Generic, TypeVar

from open_investing.order.const.order import OrderCommandName, OrderSide
from open_investing.task.task_command import TaskCommand, SubCommand
from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler
from open_library.locator.service_locator import ServiceKey
import logging

logger = logging.getLogger(__name__)


class OrderSpec(TaskSpec):
    spec_type_name_classvar: ClassVar[str]
    spec_type_name: str

    strategy_name: str
    strategy_session_id: UUID

    # non hashed
    decision_id: UUID
    order_side: OrderSide
    order_id: UUID | None
    offsetted_order_id: UUID | None = None
    is_offset: bool = False
    parent_order_id: UUID | None = None
    price: Money | None = None

    security_code: str
    quantity_multiplier: Decimal
    quantity_exposure: Decimal

    def __hash__(self):
        attrs_hash = map(
            hash, (self.spec_type_name, self.strategy_name, self.strategy_session_id)
        )
        return functools.reduce(operator.xor, attrs_hash, 0)


class OrderCommand(SubCommand):
    name: OrderCommandName


class OrderTaskCommand(TaskCommand):
    order_command: OrderCommand

    @property
    def sub_command(self) -> OrderCommand:
        return self.order_command


T = TypeVar("T", bound=OrderSpec)


class OrderAgent(Generic[T], TaskSpecHandler):
    task_spec_cls: Type[OrderSpec]

    def __init__(self, order_spec: OrderSpec):
        super().__init__(order_spec)

        self.command_queue = asyncio.Queue()
        self.order_event_queue = asyncio.Queue()
        self.quote_event_queue = asyncio.Queue()

        self.tasks = dict(
            run_order_command=Task("run_order_command", self.run_order_command()),
            run_order_event=Task("run_order_event", self.run_order_event()),
        )
        self.running_order_command = False
        self.running_order_event = False

    @property
    def order_spec(self) -> T:
        return cast(T, self.task_spec)

    @property
    def name(self):
        return self.task_spec_cls.spec_type_name_classvar

    async def on_order_command(self, order_info):
        pass

    async def run_order_command(self):
        self.running_order_command = True
        while True:
            try:
                order_info = await self.command_queue.get()

                await self.on_order_command(order_info)
            except Exception as e:
                logger.exception(f"run_order_command: {e}")

    async def enqueue_order_command(self, order_info):
        await self.command_queue.put(order_info)

    enqueue_command = enqueue_order_command

    async def on_order_event(self, order_event):
        pass

    async def run_order_event(self):
        self.running_order_event = True
        while True:
            try:
                order_event = await self.order_event_queue.get()

                await self.on_order_event(order_event)
            except Exception as e:
                logger.exception(f"run_order_event: {e}")

    async def enqueue_order_event(self, order_event):
        await self.order_event_queue.put(order_event)

    async def on_quote_event(self, quote_event):
        pass

    async def run_quote_event(self):
        while True:
            try:
                quote_event = await self.quote_event_queue.get()

                await self.on_quote_event(quote_event)
            except Exception as e:
                logger.exception(f"run_quote_event: {e}")

    async def enqueue_quote_event(self, event):
        await self.quote_event_queue.put(event)

    @property
    def order_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Order.Order"},
        )
        order_data_manager = self.services[service_key]
        return order_data_manager

    @property
    def order_event_broker(self):
        service_key = ServiceKey(
            service_type="pubsub_broker",
            service_name="order_event_broker",
        )

        return self.services[service_key]

    @property
    def quote_event_broker(self):
        service_key = ServiceKey(
            service_type="pubsub_broker",
            service_name="quote_event_broker",
        )

        service = self.services[service_key]
        return service

    @property
    def order_service(self):
        service_key = ServiceKey(
            service_type="service",
            service_name="order_service",
        )

        return self.services[service_key]

    @property
    def quote_service(self):
        service_key = ServiceKey(
            service_type="service",
            service_name="quote_service",
        )

        return self.services[service_key]

    @property
    def exchange_manager(self):
        service_key = self.task_spec.get_service_key(name="exchange_api_manager")
        return self.services[service_key]

    @property
    def order_task_dispatcher(self):
        service_key = self.task_spec.get_service_key(name="order_task_dispatcher")
        return self.services[service_key]

    @property
    def base_spec_dict(self):
        from open_library.collections.dict import instance_to_dict

        spec_dict = instance_to_dict(
            self.order_spec, ["strategy_name", "strategy_session_id", "decision_id"]
        )

        spec_dict["parent_order_id"] = self.order_spec.order_id
        return spec_dict

    @property
    def app_config(self):
        service_key = self.task_spec.get_service_key(name="app_config")

        return self.services[service_key]
