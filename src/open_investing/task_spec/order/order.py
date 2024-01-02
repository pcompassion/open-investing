#!/usr/bin/env python3

from typing import Any
from typing import ClassVar, Type
from pydantic import BaseModel
from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler
from open_investing.task.task_command import TaskCommand


class OrderSpec(TaskSpec):
    spec_type_name_classvar: ClassVar[str]

    strategy_name: str
    strategy_session_id: str

    # non hashed
    decision_id: str

    security_code: str
    amount: float

    def __hash__(self):
        attrs_hash = map(
            hash, (self.spec_type_name, self.strategy_name, self.strategy_session_id)
        )
        return attrs_hash


class OrderCommand(TaskCommand):
    name: str


class OrderAgent(TaskSpecHandler):
    task_spec_cls: Type[OrderSpec]

    @property
    def order_spec(self):
        return self.task_spec

    @property
    def name(self):
        return self.task_spec_cls.spec_type_name_classvar
