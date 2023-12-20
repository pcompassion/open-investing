#!/usr/bin/env python3
from abc import ABC, abstractmethod
from typing import Dict, Union, Optional, Type

from open_library.extension.croniter_ex import estimate_interval, estimate_timeframe
from open_library.time.const import TimeUnit

from pydantic import BaseModel, root_validator, ValidationError


# Base TaskSpec class
class TaskSpec(BaseModel):
    # Common fields for all TaskSpec

    spec_type_name: str = ""
    cron_time: Optional[str]
    data: Dict[str, Union[str, int, float]] = {}

    # @root_validator(pre=True)
    # @classmethod
    # def check_spec_type_name(cls, values):
    #     if "spec_type_name" not in values:
    #         raise ValidationError("spec_type_name must be defined")
    #     return values

    def estimated_interval(self, time_unit: TimeUnit = TimeUnit.SECOND):
        if self.cron_time:
            return estimate_interval(self.cron_time, time_unit=time_unit)

        return 0

    def estimated_timeframe(self, base_time=None):
        if self.cron_time:
            return estimate_timeframe(self.cron_time, base_time=base_time)

        return 0


class TaskSpecHandler(ABC):
    task_spec_cls: Optional[Type[TaskSpec]] = None

    def __init__(self, task_spec: TaskSpec):
        self.task_spec = task_spec
        self.listeners = []

    # @classmethod
    # @abstractmethod
    # def task_spec_cls(cls):
    #     if not hasattr(cls, "task_spec_cls"):
    #         raise NotImplementedError(
    #             "Subclass must have a class variable 'task_spec_cls'"
    #         )
    #     if not isinstance(
    #         getattr(cls, "task_spec_cls"), TaskSpec
    #     ):  # replace 'int' with the expected type
    #         raise TypeError("'task_spec_cls' must be an TaskSpec")

    def subscribe(self, listener):
        if listener not in self.listeners:
            self.listeners.append(listener)

    def unsubscribe(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    async def notify_listeners(self, message):
        for listener in self.listeners:
            await listener(message)
