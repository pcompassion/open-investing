#!/usr/bin/env python3
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, List, Optional, Type, Union

from open_library.extension.croniter_ex import estimate_interval, estimate_timeframe
from open_library.time.const import TimeUnit

from pydantic import BaseModel, root_validator, ValidationError
from open_investing.task.task import Task
from open_investing.locator.service_locator import ServiceKey


# Base TaskSpec class
class TaskSpec(BaseModel):
    spec_type_name_classvar: ClassVar[str]

    spec_type_name: str = ""
    cron_time: str | None = None
    data: dict[str, Union[str, int, float]] = {}
    service_keys: dict[str, ServiceKey] = {}

    # provide default value
    default_service_keys: ClassVar[dict[str, ServiceKey]] = {}

    def __hash__(self):
        return hash((type(self),) + tuple(sorted(self.__dict__.items())))

    def estimated_interval(self, time_unit: TimeUnit = TimeUnit.SECOND):
        if self.cron_time:
            return estimate_interval(self.cron_time, time_unit=time_unit)

        return 0

    def estimated_timeframe(self, base_time=None):
        if self.cron_time:
            return estimate_timeframe(self.cron_time, base_time=base_time)

        return 0

    def get_service_key(self, name: str | None = None, **kwargs):
        service_keys = self.default_service_keys | self.service_keys
        if name:
            return service_keys.get(name)

        service_key_dict = kwargs

        lookup_service_key = ServiceKey(**service_key_dict)

        for _, service_key in service_keys.items():
            if service_key == lookup_service_key:
                return service_key

        return None

    @classmethod
    def set_default_service_keys(cls, service_keys):
        cls.default_service_keys = service_keys

    @classmethod
    def get_default_service_key(cls, name: str | None = None, **kwargs):
        service_keys = cls.default_service_keys
        if name:
            return service_keys.get(name)

        service_key_dict = kwargs

        lookup_service_key = ServiceKey(**service_key_dict)

        for _, service_key in service_keys.items():
            if service_key == lookup_service_key:
                return service_key

        return None

    def get_service_keys(self):
        return self.default_service_keys | self.service_keys


class TaskSpecHandler(ABC):
    task_spec_cls: Type[TaskSpec]

    def __init__(self, task_spec: TaskSpec):
        self.task_spec = task_spec
        self.listeners = []
        self.tasks: dict[str, Task] = {}
        self.running = False

        self.services = {}

    def subscribe(self, listener):
        if listener not in self.listeners:
            self.listeners.append(listener)

    def unsubscribe(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    async def notify_listeners(self, message):
        for listener in self.listeners:
            await listener(message)

    async def start_tasks(self):
        for k, task in self.tasks.items():
            await task.start()
        self.running = True

    async def stop_tasks(self):
        self.running = False

    def set_service(self, service_key: ServiceKey, service):
        self.services[service_key] = service

    async def init(self):
        pass

    @property
    def name(self) -> str:
        return self.task_spec_cls.spec_type_name_classvar

    def is_running(self) -> bool:
        return self.running
