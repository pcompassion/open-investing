#!/usr/bin/env python3

from open_library.observe.listener_spec import ListenerSpec
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

from open_library.app.base_app import BaseApp
from open_library.locator.service_locator import ServiceKey, ServiceLocator
from open_investing.exchange.ebest.api_manager import EbestApiManager
from open_investing.order.order_event_broker import OrderEventBroker
from open_investing.order.quote_event_broker import QuoteEventBroker
from open_investing.strategy.decision_event_broker import DecisionEventBroker
from open_investing.order.order_service import OrderService
from open_investing.task.const import TaskCommandName
from open_investing.security.quote_service import QuoteService
from open_library.app.config import BaseConfig


async def debug_control():
    while True:
        await asyncio.sleep(1)


class App(BaseApp):
    name = "base_app"

    def __init__(self, env_directory, env_file, config: BaseConfig):
        super().__init__(env_directory=env_directory, env_file=env_file)

        self._service_locator = ServiceLocator()
        self.task_manager = TaskManager(self._service_locator)
        self.task_dispatcher = None

        config.initialize(self.environment)
        self.config = config

        self.tasks = []
        self.setup_django()

    async def init(self):
        self.setup_default_service_keys()
        await self.setup_service_manager()

        import_modules = [
            "risk_glass.market_event",
            "risk_glass.strategy",
            "open_investing.order.agent",
            "open_investing.strategy.decision",
        ]

        for module in import_modules:
            importlib.import_module(module)

        ListenerSpec.set_service_locator(self._service_locator)

    def setup_default_service_keys(self):
        from .after_django import (
            MarketIndicatorDataManager,
            NearbyFutureDataManager,
            FutureDataManager,
            OptionDataManager,
            DecisionDataManager,
            StrategySessionDataManager,
            OrderDataManager,
        )

        TaskSpec.set_default_service_keys(
            {
                "exchange_api_manager": EbestApiManager.service_key,
                "market_event_task_dispatcher": LocalTaskDispatcher.service_key,
                "order_task_dispatcher": LocalTaskDispatcher.service_key,
                "decision_task_dispatcher": LocalTaskDispatcher.service_key,
                "order_event_broker": OrderEventBroker.service_key,
                "quote_event_broker": QuoteEventBroker.service_key,
                "decision_event_broker": DecisionEventBroker.service_key,
                "order_service": OrderService.service_key,
                "quote_service": QuoteService.service_key,
                "app_config": self.config.service_key,
                uuid4(): MarketIndicatorDataManager.service_key,
                uuid4(): NearbyFutureDataManager.service_key,
                uuid4(): FutureDataManager.service_key,
                uuid4(): OptionDataManager.service_key,
                uuid4(): DecisionDataManager.service_key,
                uuid4(): StrategySessionDataManager.service_key,
                uuid4(): OrderDataManager.service_key,
            }
        )

    async def setup_service_manager(self):
        from .after_django import (
            MarketIndicatorDataManager,
            NearbyFutureDataManager,
            FutureDataManager,
            OptionDataManager,
            DecisionDataManager,
            StrategySessionDataManager,
            OrderDataManager,
        )

        service_locator = self._service_locator

        local_task_dispatcher = LocalTaskDispatcher(self.task_manager)
        local_task_dispatcher.init()
        service_locator.register_service(
            local_task_dispatcher.service_key, local_task_dispatcher
        )

        ebest_api_manager = EbestApiManager()
        await ebest_api_manager.initialize(self.environment)
        service_locator.register_service(
            ebest_api_manager.service_key, ebest_api_manager
        )

        order_event_broker = OrderEventBroker()
        order_event_broker.init()
        service_locator.register_service(
            order_event_broker.service_key, order_event_broker
        )

        quote_event_broker = QuoteEventBroker()
        quote_event_broker.init()
        service_locator.register_service(
            quote_event_broker.service_key, quote_event_broker
        )

        decision_event_broker = DecisionEventBroker()
        decision_event_broker.init()
        service_locator.register_service(
            decision_event_broker.service_key, decision_event_broker
        )

        market_indicator_data_manager = MarketIndicatorDataManager()
        market_indicator_data_manager.initialize(self.environment)
        service_locator.register_service(
            market_indicator_data_manager.service_key, market_indicator_data_manager
        )

        nearby_future_data_manager = NearbyFutureDataManager()
        nearby_future_data_manager.initialize(self.environment)
        service_locator.register_service(
            nearby_future_data_manager.service_key, nearby_future_data_manager
        )

        future_data_manager = FutureDataManager()
        future_data_manager.initialize(self.environment)
        service_locator.register_service(
            future_data_manager.service_key, future_data_manager
        )

        option_data_manager = OptionDataManager()
        option_data_manager.initialize(self.environment)
        service_locator.register_service(
            option_data_manager.service_key, option_data_manager
        )

        decision_data_manager = DecisionDataManager()
        # decision_data_manager.initialize(self.environment)
        service_locator.register_service(
            decision_data_manager.service_key, decision_data_manager
        )

        strategy_session_data_manager = StrategySessionDataManager()
        # strategy_session_data_manager.initialize(self.environment)
        service_locator.register_service(
            strategy_session_data_manager.service_key, strategy_session_data_manager
        )

        order_data_manager = OrderDataManager()
        # order_data_manager.initialize(self.environment)
        service_locator.register_service(
            order_data_manager.service_key, order_data_manager
        )

        ebest_api_manager.set_order_event_broker(order_event_broker)
        ebest_api_manager.set_order_data_manager(order_data_manager)

        order_service = OrderService()
        await order_service.initialize()
        service_locator.register_service(order_service.service_key, order_service)

        order_service.set_order_event_broker(order_event_broker)
        order_service.set_order_data_manager(order_data_manager)
        order_service.set_exchange_manager(ebest_api_manager)

        quote_service = QuoteService()
        await quote_service.initialize()
        quote_service.set_exchange_manager(ebest_api_manager)

        service_locator.register_service(quote_service.service_key, quote_service)

        config = self.config
        service_locator.register_service(config.service_key, config)

    def setup_django(self):
        import django

        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE", self.environment.get("DJANGO_SETTINGS_MODULE")
        )

        os.environ.setdefault(
            "DJANGO_ALLOW_ASYNC_UNSAFE",
            self.environment.get("DJANGO_ALLOW_ASYNC_UNSAFE") or "true",
        )

        django.setup()

    def get_service_locator(self):
        return self._service_locator

    def get_service(self, service_key):
        service = self._service_locator.get_service(service_key)
        return service
