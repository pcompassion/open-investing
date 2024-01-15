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
from open_investing.config.base import STRATEGY_CHANNEL_NAME, redis_config
from open_investing.order.order_event_broker import OrderEventBroker
from open_investing.order.order_service import OrderService
from open_investing.task.const import TaskCommandName
from open_investing.security.quote_service import QuoteService


async def debug_control():
    while True:
        await asyncio.sleep(1)


class App(BaseApp):
    name = "task_app"

    def __init__(self, env_directory=Path(), env_file=".env.dev"):
        super().__init__(env_directory=env_directory, env_file=env_file)

        self.task_manager = TaskManager(self._service_locator)
        self.task_dispatcher = None

        self.tasks = []

    def setup_base_tasks(self):
        tasks = self.tasks

        task_manager = self.task_manager
        tasks.append(asyncio.create_task(task_manager.run()))

        redis_client = aioredis.from_url(**redis_config["strategy"])

        receiver = RedisTaskReceiver(task_manager, STRATEGY_CHANNEL_NAME, redis_client)
        tasks.append(asyncio.create_task(receiver.run()))

    async def main(self):
        await self.init()

        self.setup_base_tasks()

        await self.start_strategies()

        if self.environment.is_dev():
            self.tasks.append(asyncio.create_task(debug_control()))

        await asyncio.gather(*self.tasks)

    async def init(self):
        await super().init()

        self.task_dispatcher = LocalTaskDispatcher(self.task_manager)
        await self.task_dispatcher.init()

    async def start_strategies(self):
        from open_investing.task_spec.task_spec_handler_registry import (
            TaskSpecHandlerRegistry,
        )

        running_strategies = defaultdict(int)

        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Strategy.StrategySession"},
        )
        strategy_session_data_manager = self.get_service(service_key)

        # strategy_sessions = (
        #     await strategy_session_data_manager.ongoing_strategy_sessions()
        # )

        # for strategy_session in strategy_sessions:
        #     strategy_name = strategy_session.strategy_name

        #     task_spec_dict = {
        #         "spec_type_name": strategy_name,
        #         "strategy_session_id": strategy_session.id,
        #     }
        #     task_spec = TaskSpecHandlerRegistry.create_spec_instance(task_spec_dict)

        #     command = TaskCommand(name=TaskCommandName.Start)
        #     await self.task_dispatcher.dispatch_task(task_spec, command)

        #     running_strategies[strategy_name] += 1

        if "delta_hedge" not in running_strategies:
            task_spec_dict = {
                "spec_type_name": "strategy.delta_hedge",
                "strategy_session_id": uuid4(),
            }
            task_spec = TaskSpecHandlerRegistry.create_spec_instance(task_spec_dict)

            command = TaskCommand(name=TaskCommandName.Start)

            await self.task_dispatcher.dispatch_task(task_spec, command)
