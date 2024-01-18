#!/usr/bin/env python3
from uuid import uuid4
from open_investing.task_spec.task_spec import TaskSpec
import asyncio
import os
import importlib
from open_investing.task.task_manager import TaskManager
from open_investing.task.task_dispatcher import LocalTaskDispatcher
from open_investing.task.task_receiver import RedisTaskReceiver

from redis import asyncio as aioredis
from open_library.environment.environment import Environment

from open_library.app.base_app import BaseApp
from open_library.locator.service_locator import ServiceLocator
from open_investing.exchange.ebest.api_manager import EbestApiManager
from open_investing.app.base_app import App as BaseApp


async def debug_control():
    while True:
        await asyncio.sleep(1)


class App(BaseApp):
    name = "test_app"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.added_tasks = []

    async def init(self):
        await super().init()
