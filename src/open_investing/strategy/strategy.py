#!/usr/bin/env python3
from typing import cast
from open_investing.locator.service_locator import ServiceKey
import functools
import operator
import itertools

from abc import ABC, abstractmethod
from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler

# from open_investing.strategy.models.decision import Decision


class StrategySpec(TaskSpec):
    strategy_name: str | None = None
    session_id: int | None = None

    def __hash__(self):
        attrs_hash = map(hash, (self.strategy_name, self.session_id))
        data_items_hash = map(hash, tuple(self.data.items()))
        combined_hashes = itertools.chain(attrs_hash, data_items_hash)
        return functools.reduce(operator.xor, combined_hashes, 0)


class Strategy(TaskSpecHandler):
    def __init__(self, task_spec: StrategySpec) -> None:
        super().__init__(task_spec)

    @property
    def strategy_spec(self) -> StrategySpec:
        return cast(StrategySpec, self.task_spec)  # convenient

    @property
    def decision_task_dispatcher(self):
        service_key = self.task_spec.get_service_key(name="decision_task_dispatcher")
        return self.services[service_key]

    @property
    def decision_data_manager(self):
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
