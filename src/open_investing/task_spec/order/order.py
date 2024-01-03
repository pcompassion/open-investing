#!/usr/bin/env python3

from typing import Any
from typing import ClassVar, Type
from pydantic import BaseModel
from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler
from open_investing.task.task_command import TaskCommand
from open_investing.order.const.order import OrderCommandName


class OrderSpec(TaskSpec):
    spec_type_name_classvar: ClassVar[str]

    strategy_name: str
    strategy_session_id: str

    # non hashed
    decision_id: str

    security_code: str
    quantity: float

    def __hash__(self):
        attrs_hash = map(
            hash, (self.spec_type_name, self.strategy_name, self.strategy_session_id)
        )
        return attrs_hash


class OrderCommand(TaskCommand):
    name: OrderCommandName


class OrderAgent(TaskSpecHandler):
    task_spec_cls: Type[OrderSpec]

    def __init__(self, order_spec: OrderSpec):
        super().__init__(order_spec)

        self.command_queue = asyncio.Queue()
        self.order_event_queue = asyncio.Queue()

        service_key = self.task_spec.get_service_key(name="order_event_broker")
        self.order_event_broker = self.services[service_key]

    @property
    def order_spec(self):
        return self.task_spec

    @property
    def name(self):
        return self.task_spec_cls.spec_type_name_classvar

    async def on_order_command(order_info):
        pass

    async def on_order_event(order_event):
        pass

    async def run_command(self):
        while True:
            order_info = await self.command_queue.get()

            await self.on_order_command(order_info)

    async def run_order_event(self):
        while True:
            order_event = await self.order_event_queue.get()

            await self.on_order_event(order_event)

    async def enqueue_order_command(self, order_info):
        await self.command_queue.put(order_info)

    async def enqueue_order_event(self, order_event):
        await self.order_event_queue.put(order_event)
