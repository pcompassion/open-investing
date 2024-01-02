#!/usr/bin/env python3
import functools
import operator
import itertools

from abc import ABC, abstractmethod
from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler

# from open_investing.strategy.models.decision import Decision


class StrategySpec(TaskSpec):
    strategy_type: str | None = None
    session_id: int | None = None

    def __hash__(self):
        attrs_hash = map(hash, (self.strategy_type, self.session_id))
        data_items_hash = map(hash, tuple(self.data.items()))
        combined_hashes = itertools.chain(attrs_hash, data_items_hash)
        return functools.reduce(operator.xor, combined_hashes, 0)


class IStrategy(TaskSpecHandler):
    def __init__(self, task_spec: StrategySpec) -> None:
        super().__init__(task_spec)

    @property
    def strategy_spec(self):
        return self.task_spec  # convenient
