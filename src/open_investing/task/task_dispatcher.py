#!/usr/bin/env python3

from open_investing.locator.service_locator import ServiceKey
from collections import defaultdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from open_investing.task.const import ListenerType
from open_investing.task.task_manager import TaskManager
from open_investing.task_spec.task_spec import TaskSpec


class TaskDispatcher(ABC):
    def __init__(self):
        self.listeners = defaultdict(list)

    @abstractmethod
    async def dispatch_task(self, task_spec, command):
        pass

    @abstractmethod
    def subscribe(
        self, task_spec, listener, listener_type: ListenerType = ListenerType.Callable
    ):
        pass

    @abstractmethod
    async def notify_listeners(self, message):
        pass

    @classmethod
    def create_task_id(cls):
        return str(uuid.uuid4())


class DummyTaskDispatcher(TaskDispatcher):
    def __init__(self):
        super().__init__()

    async def dispatch_task(self, task_spec: TaskSpec, command):
        pass

    def subscribe(
        self, task_spec: TaskSpec, listener, listner_type=ListenerType.Callable
    ):
        pass

    async def notify_listeners(self, message):
        pass


class LocalTaskDispatcher(TaskDispatcher):
    service_key = ServiceKey(
        service_type="task_dispatcher",
        service_name="local",
    )

    def __init__(self, task_manager: TaskManager):
        super().__init__()
        self.task_manager = task_manager

    async def dispatch_task(self, task_spec: TaskSpec, command):
        task_info = {"command": command, "task_spec": task_spec}
        self.task_manager.subscribe_all(self.notify_listeners)
        await self.task_manager.enqueue_task_command(task_info)

    def subscribe(
        self, task_spec: TaskSpec, listener, listener_type=ListenerType.Callable
    ):
        if listener not in self.listeners[task_spec]:
            self.listeners[task_spec].append(listener)

    def unsubscribe(
        self, task_spec: TaskSpec, listener, listener_type=ListenerType.Callable
    ):
        if listener in self.listeners[task_spec]:
            self.listeners[task_spec].remove(listener)

    async def notify_listeners(self, message):
        task_spec = message["task_spec"]

        listeners = self.listeners[task_spec]
        for listener in listeners:
            await listener(message)
