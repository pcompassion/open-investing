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
from open_investing.locator.service_locator import ServiceLocator
from open_investing.exchange.ebest.api_manager import EbestApiManager
from open_investing.config.base import STRATEGY_CHANNEL_NAME, redis_config


async def debug_control():
    while True:
        await asyncio.sleep(1)


class App(BaseApp):
    name = "task_app"

    def __init__(self):
        self.environment = Environment(env_file=".env.dev")

        self._service_locator = ServiceLocator()
        self.task_manager = TaskManager(self._service_locator)
        self.task_dispatcher = LocalTaskDispatcher(self.task_manager)
        self.tasks = []

    def setup_base_tasks(self):
        tasks = self.tasks

        task_manager = self.task_manager
        tasks.append(asyncio.create_task(task_manager.run()))

        redis_client = aioredis.from_url(**redis_config["strategy"])

        receiver = RedisTaskReceiver(task_manager, STRATEGY_CHANNEL_NAME, redis_client)
        tasks.append(asyncio.create_task(receiver.run()))

    async def main(self):
        self.init()

        self.setup_base_tasks()

        await self.start_strategies()

        if self.environment.is_dev():
            self.tasks.append(asyncio.create_task(debug_control()))

        await asyncio.gather(*self.tasks)

    def init(self):
        """initialize app, runs before main"""
        self.setup_logging()
        self.setup_django()

        self.setup_default_service_keys()
        self.setup_service_manager()

        import_modules = [
            "risk_glass.market_event",
            "risk_glass.strategy",
        ]

        for module in import_modules:
            importlib.import_module(module)

    def setup_default_service_keys(self):
        from .after_django import (
            NearbyFutureDataManager,
            FutureDataManager,
            OptionDataManager,
            MarketIndicatorDataManager,
        )

        TaskSpec.set_default_service_keys(
            {
                "exchange_api_manager": EbestApiManager.service_key,
                uuid4(): NearbyFutureDataManager.service_key,
                uuid4(): FutureDataManager.service_key,
                uuid4(): OptionDataManager.service_key,
                "market_event_task_dispatcher": LocalTaskDispatcher.service_key,
                uuid4(): MarketIndicatorDataManager.service_key,
            }
        )

    def setup_service_manager(self):
        from .after_django import (
            NearbyFutureDataManager,
            FutureDataManager,
            OptionDataManager,
            MarketIndicatorDataManager,
        )

        service_locator = self._service_locator

        service_locator.register_service(
            LocalTaskDispatcher.service_key, self.task_dispatcher
        )

        ebest_api_manager = EbestApiManager()
        ebest_api_manager.initialize(self.environment)
        service_locator.register_service(
            ebest_api_manager.service_key, ebest_api_manager
        )

        nearby_future_manager = NearbyFutureDataManager()
        nearby_future_manager.initialize(self.environment)
        service_locator.register_service(
            nearby_future_manager.service_key, nearby_future_manager
        )

        future_manager = FutureDataManager()
        future_manager.initialize(self.environment)
        service_locator.register_service(future_manager.service_key, future_manager)

        option_manager = OptionDataManager()
        option_manager.initialize(self.environment)
        service_locator.register_service(option_manager.service_key, option_manager)

        market_indicator_manager = MarketIndicatorDataManager()
        market_indicator_manager.initialize(self.environment)
        service_locator.register_service(
            market_indicator_manager.service_key, market_indicator_manager
        )

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

        task_spec_dict = {
            "spec_type_name": "dynamic_hedge",
        }
        task_spec = TaskSpecHandlerRegistry.create_spec_instance(task_spec_dict)

        command = "start"
        await self.task_dispatcher.dispatch_task(task_spec, command)

    def get_service_locator(self):
        return self._service_locator

    def get_service(self, service_key):
        service = self._service_locator.get_service(service_key)
        return service

    # def setup_strategy(self):
    #     from open_investing.strategy.strategy_factory import StrategyFactory
    #     from risk_glass.strategy.dynamic_hedge import DynamicHedgeStrategy

    #     StrategyFactory.register_class(DynamicHedgeStrategy.name, DynamicHedgeStrategy)
