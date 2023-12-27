#!/usr/bin/env python3
import asyncio
import os
from open_investing.task.task_manager import TaskManager
from open_investing.task.task_receiver import RedisTaskReceiver

from redis import asyncio as aioredis
from open_library.environment.environment import Environment

from open_investing.exchange.store import ExchangeStore


async def debug_control():
    while True:
        await asyncio.sleep(1)


class App:
    name = "task_app"

    def __init__(self):
        self.exchange_store = ExchangeStore()

        self.environment = Environment(env_file=".env.dev")

    async def main(self):
        from risk_glass.settings.task_app import STRATEGY_CHANNEL_NAME, redis_config

        task_manager = TaskManager()
        asyncio.create_task(task_manager.run())

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

    def setup_logging(self):
        log_to_file = self.environment.get("LOG_TO_FILE", False)
        log_dir_path = self.environment.cur_directory / "logs"

        local_timezone = self.environment.local_timezone

        from open_library.logging.loggings import setup_logging

        setup_logging(
            log_dir_path, log_to_file=log_to_file, app_name=self.name, tz=local_timezone
        )

    def setup_strategy(self):
        from open_investing.strategy.strategy_factory import StrategyFactory
        from risk_glass.strategy.dynamic_hedge import DynamicHedgeStrategy

        StrategyFactory.register_class(DynamicHedgeStrategy.name, DynamicHedgeStrategy)

    def setup_django(self):
        import django

        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", self.environment.get("DJANGO_SETTINGS_MODULE")
        )

        django.setup()


app = App()
