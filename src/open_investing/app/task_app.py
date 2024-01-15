#!/usr/bin/env python3

from open_investing.task.task_command import TaskCommand
from collections import defaultdict
from uuid import uuid4
from pathlib import Path

import asyncio
import os
import importlib
from open_investing.task.task_manager import TaskManager
from open_investing.task.task_dispatcher import LocalTaskDispatcher
from open_investing.task.task_receiver import RedisTaskReceiver
from open_investing.task_spec.task_spec import TaskSpec
from redis import asyncio as aioredis
from open_library.environment.environment import Environment


from open_investing.app.base_app import App as BaseApp
from open_library.locator.service_locator import ServiceKey, ServiceLocator
from open_investing.exchange.ebest.api_manager import EbestApiManager

from open_investing.order.order_event_broker import OrderEventBroker
from open_investing.order.order_service import OrderService
from open_investing.task.const import TaskCommandName
from open_investing.security.quote_service import QuoteService

from open_investing.config.task import Config


async def debug_control():
    while True:
        await asyncio.sleep(1)


class App(BaseApp):
    name = "task_app"

    def __init__(self, env_directory=Path(), env_file=".env.cafe24"):
        super().__init__(env_directory=env_directory, env_file=env_file)
        self.config = Config(self.environment)

        self.task_manager = TaskManager(self._service_locator)

        self.tasks = []

    def setup_base_tasks(self):
        tasks = self.tasks

        task_manager = self.task_manager
        tasks.append(asyncio.create_task(task_manager.run()))

        redis_config = self.config.redis_config
        STRATEGY_CHANNEL_NAME = self.config.STRATEGY_CHANNEL_NAME

        redis_client = aioredis.from_url(**redis_config["strategy"])

        receiver = RedisTaskReceiver(task_manager, STRATEGY_CHANNEL_NAME, redis_client)
        tasks.append(asyncio.create_task(receiver.run()))

    async def main(self):
        await self.init()

        self.setup_base_tasks()

        if self.environment.is_dev():
            self.tasks.append(asyncio.create_task(debug_control()))

        await asyncio.gather(*self.tasks)

    async def init(self):
        await super().init()
