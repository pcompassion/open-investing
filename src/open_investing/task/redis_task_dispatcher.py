#!/usr/bin/env python3
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
    def subscribe(self, task_spec, listener, listener_type=ListenerType.Callable):
        raise NotImplementedError

    @subscribe.register(TaskSpec)
    def _(self, task_spec: TaskSpec, listener, listener_type=ListenerType.Callable):
        self.subscribe(task_spec.model_dump(), listener, listener_type)

    @subscribe.register(dict)
    def _(self, task_spec, listener, listener_type=ListenerType.Callable):
        # task_spec_h = hashable_json(task_spec)
        task_spec_h = task_spec["spec_type_name"]
        listener_pair = (listener, listener_type)
        if listener_pair not in self.listeners[task_spec_h]:
            self.listeners[task_spec_h].append(listener_pair)

    async def notify_listeners(self, message):
        task_spec = message["task_spec"]

        task_spec_h = task_spec["spec_type_name"]

        # task_spec_h = hashable_json(task_spec)

        listeners = self.listeners[task_spec_h]

        for listener, listener_type in listeners:
            match listener_type:
                case ListenerType.Callable:
                    await listener(task_spec, message)
                case ListenerType.ChannelGroup:
                    channel_layer = get_channel_layer()
                    group_name = listener
                    await channel_layer.group_send(
                        group_name, {"type": "task_message", "message": message}
                    )

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
