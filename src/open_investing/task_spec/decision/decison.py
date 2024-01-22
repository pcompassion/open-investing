#!/usr/bin/env python3

import operator
import functools
from uuid import UUID
import asyncio
from open_library.locator.service_locator import ServiceKey
from typing import Any, cast
from typing import ClassVar, Type
from pydantic import BaseModel
from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler
from open_investing.task.task_command import SubCommand, TaskCommand
from open_investing.strategy.const.decision import DecisionCommandName
from typing import Generic, TypeVar
import logging

logger = logging.getLogger(__name__)


class DecisionSpec(TaskSpec):
    spec_type_name_classvar: ClassVar[str]

    strategy_name: str
    strategy_session_id: UUID

    decision_id: UUID

    def __hash__(self):
        attrs_hash = map(
            hash, (self.spec_type_name, self.strategy_name, self.strategy_session_id)
        )
        return functools.reduce(operator.xor, attrs_hash, 0)


class DecisionCommand(SubCommand):
    name: DecisionCommandName


class DecisionTaskCommand(TaskCommand):
    decision_command: DecisionCommand

    @property
    def sub_command(self) -> DecisionCommand:
        return self.decision_command


T = TypeVar("T", bound=DecisionSpec)


class DecisionHandler(Generic[T], TaskSpecHandler):
    task_spec_cls: Type[DecisionSpec]

    def __init__(self, decision_spec: DecisionSpec):
        super().__init__(decision_spec)

        self.command_queue = asyncio.Queue()
        self.order_event_queue = asyncio.Queue()

    @property
    def decision_spec(self) -> T:
        return cast(T, self.task_spec)

    @property
    def name(self):
        return self.task_spec_cls.spec_type_name_classvar

    @property
    def decision_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Strategy.Decision"},
        )
        decision_data_manager = self.services[service_key]
        return decision_data_manager

    @property
    def base_spec_dict(self):
        from open_library.collections.dict import instance_to_dict

        return instance_to_dict(
            self.decision_spec, ["strategy_name", "strategy_session_id", "decision_id"]
        )

    @property
    def order_task_dispatcher(self):
        service_key = self.task_spec.get_service_key(name="order_task_dispatcher")
        return self.services[service_key]

    async def enqueue_decision_command(self, decision_info):
        await self.command_queue.put(decision_info)

    enqueue_command = enqueue_decision_command

    @property
    def order_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Order.Order"},
        )

        data_manager = self.services[service_key]
        return data_manager

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

    async def on_order_event(self, order_event):
        pass

    @property
    def order_event_broker(self):
        service_key = ServiceKey(
            service_type="pubsub_broker",
            service_name="order_event_broker",
        )

        return self.services[service_key]
