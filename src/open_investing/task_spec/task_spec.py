#!/usr/bin/env python3
from abc import ABC, abstractmethod
from typing import Dict, Union

from open_library.extension.croniter_ex import estimate_interval, estimate_timeframe
from open_library.time.const import TimeUnit
from pydantic import BaseModel


# Base TaskSpec class
class TaskSpec(BaseModel):
    # Common fields for all TaskSpec

    cron_time: str
    data: Dict[str, Union[str, int, float]] = {}

    @property
    def spec_type_name(self):
        raise NotImplementedError("Subclasses should implement a type property")

    def estimated_interval(self, time_unit: TimeUnit = TimeUnit.SECOND):
        if self.cron_time:
            return estimate_interval(self.cron_time, time_unit=time_unit)

        return 0

    def estimated_timeframe(self, base_time=None):
        if self.cron_time:
            return estimate_timeframe(self.cron_time, base_time=base_time)

        return 0


class TaskSpecHandler(ABC):
    @property
    @abstractmethod
    def task_spec_cls(cls):
        if not hasattr(cls, "task_spec_cls"):
            raise NotImplementedError(
                "Subclass must have a class variable 'task_spec_cls'"
            )
        if not isinstance(
            getattr(cls, "task_spec_cls"), TaskSpec
        ):  # replace 'int' with the expected type
            raise TypeError("'task_spec_cls' must be an TaskSpec")

    def __init__(self, task_spec: TaskSpec):
        self.task_spec = task_spec
