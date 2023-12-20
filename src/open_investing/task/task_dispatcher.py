#!/usr/bin/env python3

from collections import defaultdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from open_investing.task.const import ListenerType


class TaskDispatcher(ABC):
    def __init__(self):
        self.listeners = defaultdict(list)

    @abstractmethod
    async def dispatch_task(self, task_spec, command):
        pass

    @abstractmethod
    def subscribe(self, task_spec, listener, listner_type: ListenerType):
        pass

    @abstractmethod
    async def notify_listeners(self, task_spec, message):
        pass

    @classmethod
    def create_task_id(cls):
        return str(uuid.uuid4())


class LocalTaskDispatcher(TaskDispatcher):
    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager

    async def dispatch_task(self, task_spec, command):
        task_info = {"command": command, "task_spec": task_spec}
        await self.task_manager.enqueue_task_command(task_info)
        await self.task_manager.subscribe_all(self.notify_listeners)

    def subscribe(self, task_spec, listener, listner_type=ListenerType.Callable):
        if listener not in self.listeners[task_spec]:
            self.listeners[task_spec].append(listener)

    async def notify_listeners(self, task_spec, message):
        listeners = self.listeners[task_spec]
        for listener in listeners:
            await listener(task_spec, message)
