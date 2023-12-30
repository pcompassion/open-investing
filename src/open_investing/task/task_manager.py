#!/usr/bin/env python3

from collections import defaultdict
import asyncio
from typing import Union, Dict

from collections import defaultdict
from open_library.collections.hashable_dict import Hashabledict

from open_investing.task_spec.task_spec_handler_registry import (
    TaskSpecHandlerRegistry,
)
from open_investing.task_spec.task_spec import TaskSpec
from open_investing.locator.service_locator import ServiceLocator


class TaskManager:
    def __init__(self, service_locator: ServiceLocator):
        self.listeners = defaultdict(list)
        self.broadcast_listeners = []

        self.task_spec_handlers = {}
        self.command_queue = asyncio.Queue()
        self.service_locator = service_locator

    def subscribe(self, task_spec, listener):
        # task_spec_h = Hashabledict(task_spec)
        task_spec_h = task_spec

        if listener not in self.listeners[task_spec_h]:
            self.listeners[task_spec].append(listener)

    def subscribe_all(self, listener):
        if listener not in self.broadcast_listeners:
            self.broadcast_listeners.append(listener)

    async def notify_listeners(self, message):
        task_spec = message["task_spec"]
        # task_spec_h = Hashabledict(task_spec)
        task_spec_h = task_spec

        listeners = self.listeners[task_spec_h]

        for listener in listeners:
            await listener(message)

        for listener in self.broadcast_listeners:
            await listener(message)

    async def start_task(self, task_spec: TaskSpec):
        task_spec_h = task_spec

        if task_spec_h not in self.task_spec_handlers:
            task_spec_handler = await TaskSpecHandlerRegistry.create_handler_instance(
                task_spec
            )

            for _, service_key in task_spec.get_service_keys().items():
                service = self.service_locator.get_service(service_key)
                task_spec_handler.set_service(service_key, service)

            task_spec_handler.subscribe(self.notify_listeners)
        else:
            task_spec_handler = self.task_spec_handlers[task_spec_h]
            await task_spec_handler.stop_tasks()

        self.task_spec_handlers[task_spec_h] = task_spec_handler
        await task_spec_handler.start_tasks()

    async def stop_task(self, task_spec: TaskSpec):
        # task_spec_h = Hashabledict(task_spec)
        task_spec_h = task_spec

        task_handler = self.task_spec_handlers.get(task_spec_h)
        if task_handler:
            await task_handler.stop_tasks()

            del self.task_spec_handlers[task_spec_h]
            task_handler.unsubscribe(self.notify_listeners)

            message = {"task_spec": task_spec, "name": "task-stopped"}

            await self.notify_listeners(message)

    async def enqueue_task_command(self, task_info):
        await self.command_queue.put(task_info)

    async def run(self):
        while True:
            # while not self.command_queue.empty():
            task_info = await self.command_queue.get()
            task_spec_ = task_info["task_spec"]

            if isinstance(task_spec_, dict):
                task_spec = TaskSpecHandlerRegistry.create_spec_instance(task_spec_)
            else:
                task_spec = task_spec_

            command = task_info["command"]

            if command == "start":
                await self.start_task(task_spec)
            elif command == "stop":
                await self.stop_task(task_spec)
