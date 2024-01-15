#!/usr/bin/env python3

from open_library.observe.pubsub_broker import PubsubBroker
import asyncio
from open_library.observe.listener_spec import ListenerSpec
from typing import Callable
from open_investing.event_spec.event_spec import EventSpec
from open_library.locator.service_locator import ServiceKey
from collections import defaultdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid

from open_library.observe.const import ListenerType

from open_investing.task.task_manager import TaskManager
from open_investing.task_spec.task_spec import TaskSpec


class TaskDispatcher(ABC):
    def __init__(self):
        self.listeners = defaultdict(list)

    @abstractmethod
    async def dispatch_task(self, task_spec, command):
        pass

    @abstractmethod
    async def subscribe(
        self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable
    ):
        pass

    @abstractmethod
    async def unsubscribe(
        self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable
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
        self, task_spec: TaskSpec, listener, listener_type=ListenerType.Callable
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

        self.pubsub_broker = PubsubBroker()
        self.pubsub_task = None

    def init(self):
        self.pubsub_task = asyncio.create_task(self.pubsub_broker.run())

    async def dispatch_task(self, task_spec: TaskSpec, command):
        task_info = {"command": command, "task_spec": task_spec}
        self.task_manager.subscribe_all(self.notify_listeners)
        await self.task_manager.enqueue_task_command(task_info)

    def subscribe(self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable):
        self.pubsub_broker.subscribe(event_spec, listener_spec)

    def unsubscribe(
        self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable
    ):
        self.pubsub_broker.unsubscribe(event_spec, listener_spec)

    async def notify_listeners(self, message):
        await self.pubsub_broker.enqueue_message(message)
