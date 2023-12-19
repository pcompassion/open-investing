#!/usr/bin/env python3

import asyncio

class TaskManager:
    def __init__(self):
        self.listeners = defaultdict(list)
        self.broadcast_listeners = []

        self.task_spec_handlers = {}
        self.command_queue = asyncio.Queue()
        self.new_command_event = asyncio.Event()

    def subscribe(self, task_spec, listener):
        if listener not in self.listeners[task_spec]:
            self.listeners[task_spec].append(listener)

    def subscribe_all(self, listener):
        if listener not in self.broadcast_listeners:
            self.broadcast_listeners.append(listener)

    async def notify_listeners(self, message):
        task_spec = message["task_spec"]

        listeners = self.listeners[task_spec]

        for listener in listeners:
            await listener(message)

        for listener in self.broadcast_listeners:
            await listener(message)

    async def start_task(self, task_spec):
        if task_spec not in self.task_spec_handlers:
            task_spec_handler_cls = self.task_spec_handlers[task_spec]
            task_spec_handler = task_spec_handler_cls(task_spec)
            task_spec_handler.subscribe(self.notify_listeners)

            self.task_spec_handlers[task_spec] = task_spec_handler

    def stop_task(self, task_spec):
        task_handler = self.task_spec_handlers.get(task_spec)
        if task_handler:
            task_handler.task.cancel()
            del self.task_spec_handlers[task_spec]

    async def enqueue_task_command(self, task_info):
        await self.command_queue.put(task_info)
        self.new_command_event.set()

    async def run(self):
        while True:
            await self.new_command_event.wait()  # Wait until a new command is added
            self.new_command_event.clear()  # Reset the event

            while not self.command_queue.empty():
                task_info = await self.command_queue.get()
                task_spec = task_info["task_spec"]

                command = task_info["command"]

                if command["type"] == "start":
                    await self.start_task(task_spec)
                elif command["type"] == "stop":
                    self.stop_task(command["name"])
