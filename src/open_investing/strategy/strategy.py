#!/usr/bin/env python3
import asyncio
from typing import Generic, TypeVar, cast
from open_library.locator.service_locator import ServiceKey
import functools
import operator
import itertools

from abc import ABC, abstractmethod
from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler

# from open_investing.strategy.models.decision import Decision
from open_investing.strategy.data_manager.protocol.decision import (
    DecisionDataManagerProtocol,
)
from uuid import UUID
from open_investing.task.task_command import SubCommand, TaskCommand
from open_investing.strategy.const.strategy import StrategyCommandName

import logging

logger = logging.getLogger(__name__)


class StrategySpec(TaskSpec):
    strategy_session_id: UUID

    @property
    def hash_keys(self):
        return super().hash_keys + ["strategy_session_id"]

    @property
    def strategy_name(self):
        return self.spec_type_name


class StrategyCommand(SubCommand):
    name: StrategyCommandName


class StrategyTaskCommand(TaskCommand):
    strategy_command: StrategyCommand

    @property
    def sub_command(self) -> StrategyCommand:
        return self.strategy_command


T = TypeVar("T", bound=StrategySpec)


class Strategy(Generic[T], TaskSpecHandler):
    def __init__(self, task_spec: StrategySpec) -> None:
        super().__init__(task_spec)
        self.command_queue = asyncio.Queue()
        self.decision_event_queue = asyncio.Queue()

    async def enqueue_command(self, strategy_info):
        await self.command_queue.put(strategy_info)

    @property
    def strategy_spec(self) -> T:
        return cast(T, self.task_spec)  # convenient

    @property
    def decision_task_dispatcher(self):
        service_key = self.task_spec.get_service_key(name="decision_task_dispatcher")
        return self.services[service_key]

    @property
    def decision_data_manager(self) -> DecisionDataManagerProtocol:
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Strategy.Decision"},
        )

        data_manager = self.services[service_key]
        return data_manager

    @property
    def market_event_task_dispatcher(self):
        service_key = self.task_spec.get_service_key(
            name="market_event_task_dispatcher"
        )
        task_dispatcher = self.services[service_key]
        return task_dispatcher

    @property
    def strategy_session_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Strategy.StrategySession"},
        )

        data_manager = self.services[service_key]
        return data_manager

    @property
    def market_indicator_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Indicator.MarketIndicator"},
        )

        data_manager = self.services[service_key]
        return data_manager

    @property
    def nearby_future_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Security.NearbyFuture"},
        )

        data_manager = self.services[service_key]
        return data_manager

    @property
    def future_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Security.Future"},
        )

        data_manager = self.services[service_key]
        return data_manager

    @property
    def option_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Security.Option"},
        )

        data_manager = self.services[service_key]
        return data_manager

    @property
    def order_data_manager(self):
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Order.Order"},
        )

        data_manager = self.services[service_key]
        return data_manager

    @property
    def decision_event_broker(self):
        service_key = ServiceKey(
            service_type="pubsub_broker",
            service_name="decision_event_broker",
        )

        service = self.services[service_key]
        return service

    async def enqueue_decision_event(self, decision_event):
        await self.decision_event_queue.put(decision_event)

    async def run_decision_event(self):
        while True:
            try:
                decision_event = await self.decision_event_queue.get()

                await self.on_decision_event(decision_event)
            except Exception as e:
                logger.exception(f"run_decision_event: {e}")

    async def on_decision_event(self, decision_event):
        pass
