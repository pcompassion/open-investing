#!/usr/bin/env python3
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


class StrategySpec(TaskSpec):
    strategy_session_id: UUID

    @property
    def hash_keys(self):
        return super().hash_keys + ["strategy_session_id"]

    @property
    def strategy_name(self):
        return self.spec_type_name


T = TypeVar("T", bound=StrategySpec)


class Strategy(Generic[T], TaskSpecHandler):
    def __init__(self, task_spec: StrategySpec) -> None:
        super().__init__(task_spec)

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
