#!/usr/bin/env python3
import asyncio
import os
from open_investing.task.task_manager import TaskManager
from open_investing.task.task_dispatcher import LocalTaskDispatcher
from open_investing.task.task_receiver import RedisTaskReceiver

from redis import asyncio as aioredis
from open_library.environment.environment import Environment

from open_investing.exchange.store import ExchangeStore
from open_library.app.base_app import BaseApp


async def debug_control():
    while True:
        await asyncio.sleep(1)


class App(BaseApp):
    name = "task_app"

    def __init__(self):
        self.exchange_store = ExchangeStore()

        self.environment = Environment(env_file=".env.dev")
        self.task_manager = TaskManager()

        self.task_dispatcher = LocalTaskDispatcher(self.task_manager)
        self.market_event_task_dispatcher = self.task_dispatcher

    async def main(self):
        from risk_glass.settings.task_app import STRATEGY_CHANNEL_NAME, redis_config

        task_manager = self.task_manager
        asyncio.create_task(task_manager.run())

        await self.start_strategies()

        redis_client = aioredis.from_url(**redis_config["strategy"])

        receiver = RedisTaskReceiver(task_manager, STRATEGY_CHANNEL_NAME, redis_client)
        tasks = [asyncio.create_task(receiver.run())]
        if self.environment.is_dev():
            tasks.append(asyncio.create_task(debug_control()))
        await asyncio.gather(*tasks)

    def init(self):
        """initialize app, runs before main"""
        self.setup_logging()
        self.setup_django()
        import risk_glass.startup.startup

        from open_investing.client_adapter.startup import StartupRegistry

        StartupRegistry.initialize_startup_classes()

    # def setup_strategy(self):
    #     from open_investing.strategy.strategy_factory import StrategyFactory
    #     from risk_glass.strategy.dynamic_hedge import DynamicHedgeStrategy

    #     StrategyFactory.register_class(DynamicHedgeStrategy.name, DynamicHedgeStrategy)

    def setup_django(self):
        import django

        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", self.environment.get("DJANGO_SETTINGS_MODULE")
        )

        django.setup()

    async def start_strategies(self):
        from open_investing.task_spec.task_spec_handler_registry import (
            TaskSpecHandlerRegistry,
        )

        task_spec_dict = {"spec_type_name": "dynamic_hedge"}
        task_spec = TaskSpecHandlerRegistry.create_spec_instance(task_spec_dict)

        command = "start"
        await self.task_dispatcher.dispatch_task(task_spec, command)


app = App()
