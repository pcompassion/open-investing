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

from open_investing.task.redis_task_dispatcher import RedisTaskDispatcher


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

    async def main(self):
        # await self.init()
        redis_config = self.config.redis_config
        STRATEGY_CHANNEL_NAME = self.config.STRATEGY_CHANNEL_NAME

        redis_client = aioredis.from_url(**redis_config["strategy"])

        task_dispatcher = RedisTaskDispatcher(STRATEGY_CHANNEL_NAME, redis_client)
        task_dispatcher.init()
        self.task_dispatcher = task_dispatcher

        await task_dispatcher.start_listening()
