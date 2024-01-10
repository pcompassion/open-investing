#!/usr/bin/env python3
from typing import Callable
from open_library.observe.listener_spec import ListenerSpec
from open_investing.event_spec.event_spec import EventSpec
from open_library.observe.pubsub_broker import PubsubBroker
from functools import singledispatchmethod
from redis import asyncio as aioredis
import asyncio
import json
import logging
from channels.layers import get_channel_layer
from open_library.collections.dict import hashable_json
from open_library.collections.hashable_dict import Hashabledict
from open_investing.task_spec.task_spec import TaskSpec

from open_library.observe.const import ListenerType


from open_investing.task.task_dispatcher import TaskDispatcher

logger = logging.getLogger(__name__)


class RedisTaskDispatcher(TaskDispatcher):
    def __init__(self, channel_name, redis_client: aioredis.Redis):
        super().__init__()
        self.channel_name = channel_name
        self.redis_client = redis_client
        self.listening_task = None
        self.pubsub_broker = PubsubBroker()  # for notifying listeners

    async def init(self):
        self.pubsub_task = asyncio.create_task(self.pubsub_broker.run())

    @singledispatchmethod
    async def dispatch_task(self, task_spec, command):
        raise NotImplementedError

    @dispatch_task.register(TaskSpec)
    async def _(self, task_spec: TaskSpec, command):
        task_json = task_spec.model_dump()

        await self.dispatch_task(task_json, command)

    @dispatch_task.register(dict)
    async def _(self, task_spec, command):
        task_info = {"task_spec": task_spec, "command": command}
        task_info_json = json.dumps(task_info)
        await self.redis_client.rpush("task_queue", task_info_json)

    @singledispatchmethod
    def subscribe(self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable):
        raise NotImplementedError

    @subscribe.register
    def _(self, event_spec: EventSpec, listener_spec):
        self.subscribe(event_spec.model_dump(), listener_spec)

    @subscribe.register
    def _(self, event_spec: dict, listener_spec):
        self.pubsub_broker.subscribe(event_spec, listener_spec)

    def unsubscribe(
        self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable
    ):
        self.pubsub_broker.unsubscribe(event_spec, listener_spec)

    async def notify_listeners(self, message):
        await self.pubsub_broker.enqueue_message(message)

    async def listen_for_task_updates(self):
        while True:
            message = await self.pubsub.get_message(
                ignore_subscribe_messages=True, timeout=None
            )
            logger.info("received pubsub message")
            if message:
                data = json.loads(message["data"].decode("utf-8"))

                await self.notify_listeners(data)

    async def start_listening(self):
        self.pubsub = pubsub = self.redis_client.pubsub()

        await pubsub.subscribe(self.channel_name)
        self.listening_task = asyncio.create_task(self.listen_for_task_updates())
