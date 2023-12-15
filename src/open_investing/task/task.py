#!/usr/bin/env python3

import asyncio
from open_library.asynch.util import wrap_func_in_coro


class Task:
    def __init__(self, name, func, cron_time=None):
        self.name = name

        coro = wrap_func_in_coro(func)
        self.coro = coro
        self.task = None
        self.running = False
        self.cron_time = cron_time

    async def start(self):
        if self.running:
            print(f"{self.name} is already running")
            return

        if self.cron_time:
            self.task = crontab(
                self.cron_time, func=self.coro, start=True, run_immediate=True
            )
        else:
            self.task = asyncio.create_task(self.run())
        self.running = True

    async def stop(self):
        if not self.running:
            return

        if self.cron_time:
            self.task.stop()
        else:
            self.task.cancel()
        self.running = False

    async def run(self):
        try:
            await self.coro
        except asyncio.CancelledError:
            pass  # Handle task cancellation
        finally:
            self.running = False

    def status(self):
        return "running" if self.running else "stopped"
