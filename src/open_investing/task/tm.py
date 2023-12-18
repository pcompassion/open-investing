#!/usr/bin/env python3

import asyncio


class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.command_queue = asyncio.Queue()
        self.new_command_event = asyncio.Event()

    async def start_task(self, name, coro):
        if name not in self.tasks:
            task = asyncio.create_task(coro)
            self.tasks[name] = task

    def stop_task(self, name):
        task = self.tasks.get(name)
        if task:
            task.cancel()
            del self.tasks[name]

    async def enqueue_task_command(self, command):
        await self.command_queue.put(command)
        self.new_command_event.set()

    async def run(self):
        while True:
            await self.new_command_event.wait()  # Wait until a new command is added
            self.new_command_event.clear()  # Reset the event

            while not self.command_queue.empty():
                command = await self.command_queue.get()

                if command["type"] == "start":
                    await self.start_task(command["name"], command["coro"])
                elif command["type"] == "stop":
                    self.stop_task(command["name"])
