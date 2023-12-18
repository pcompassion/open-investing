#!/usr/bin/env python3

import asyncio


class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.command_queue = asyncio.Queue()
        self.new_command_event = asyncio.Event()

    async def start_task(self, task_spec):
        if task_spec not in self.tasks:
            task_spec_handler_cls = task_spec_handlers[task_spec]
            task_spec_handler = task_spec_handler_cls(task_spec)

            self.tasks[task_spec] = handler

    def stop_task(self, task_spec):
        task_handler = self.tasks.get(task_spec)
        if task_handler:
            task_handler.task.cancel()
            del self.tasks[task_spec]

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
