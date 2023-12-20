#!/usr/bin/env python3
import asyncio

from open_investing.task.task_manager import TaskManager
from open_investing.task.task_receiver import RedisTaskReceiver
from risk_glass.settings.task_app import STRATEGY_CHANNEL_NAME, redis_config
from redis import asyncio as aioredis

from open_investing.exchange.store import ExchangeStore


class App:
    def __init__(self):
        self.exchange_store = ExchangeStore()

    async def main(self):
        task_manager = TaskManager()
        asyncio.create_task(task_manager.run())

        redis_client = aioredis.from_url(**redis_config["strategy"])

        receiver = RedisTaskReceiver(task_manager, STRATEGY_CHANNEL_NAME, redis_client)
        await receiver.run()
        # asyncio.create_task(receiver.run())

    def init(self):
        from open_investing.client_adapter.startup import StartupRegistry

        StartupRegistry.initialize_startup_classes()


app = App()
