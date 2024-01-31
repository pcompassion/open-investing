#!/usr/bin/env python3
import redis

from open_investing.task.task_command import TaskCommand
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
from open_investing.task_spec.task_spec_handler_registry import (
    TaskSpecHandlerRegistry,
)
from open_library.collections.dict import to_jsonable_python

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

    def init(self):
        self.pubsub_broker.init()

    @singledispatchmethod
    async def dispatch_task(self, task_spec, command):
        raise NotImplementedError

    @dispatch_task.register(TaskSpec)
    async def _(self, task_spec: TaskSpec, command):
        task_json = task_spec.model_dump()
        command_json = command.model_dump()
        try:
            await self.dispatch_task(task_json, command_json)
        except redis.exceptions.ReadOnlyError:
            logger.error(f"redis readonly error: {self.redis_client}")

    @dispatch_task.register(dict)
    async def _(self, task_spec, command):
        task_info = {"task_spec": task_spec, "command": command}
        task_info_updated = to_jsonable_python(task_info)
        task_info_json = json.dumps(task_info_updated)
        await self.redis_client.rpush("task_queue", task_info_json)

    @singledispatchmethod
    def subscribe(self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable):
        raise NotImplementedError

    @subscribe.register
    def _(self, event_spec: dict, listener_spec):
        event_spec_ = TaskSpecHandlerRegistry.create_spec_instance(event_spec)
        self.subscribe(event_spec_, listener_spec)

    @subscribe.register
    def _(self, event_spec: EventSpec, listener_spec):
        self.pubsub_broker.subscribe(event_spec, listener_spec)

    def unsubscribe(
        self, event_spec: EventSpec, listener_spec: ListenerSpec | Callable
    ):
        self.pubsub_broker.unsubscribe(event_spec, listener_spec)

    async def notify_listeners(self, message):
        await self.pubsub_broker.enqueue_message(message)

    async def listen_for_task_updates(self):
        while True:
            redis_message = await self.pubsub.get_message(
                ignore_subscribe_messages=True, timeout=None
            )
            logger.info("received pubsub message")
            if redis_message:
                message_ = json.loads(redis_message["data"].decode("utf-8"))

                event_spec_ = message_["event_spec"]

                if isinstance(event_spec_, dict):
                    event_spec = TaskSpecHandlerRegistry.create_spec_instance(
                        event_spec_
                    )

                else:
                    event_spec = event_spec_

                message = dict(event_spec=event_spec, data=message_["data"])
                await self.notify_listeners(message)

    async def start_listening(self):
        self.pubsub = pubsub = self.redis_client.pubsub()

        await pubsub.subscribe(self.channel_name)
        self.listening_task = asyncio.create_task(self.listen_for_task_updates())
