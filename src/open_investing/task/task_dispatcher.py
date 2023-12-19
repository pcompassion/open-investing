#!/usr/bin/env python3

from abc import ABC, abstractmethod


class TaskDispatcher(ABC):
    def __init__(self):
        self.listeners = defaultdict(list)

    @abstractmethod
    async def dispatch_task(self, command, task_spec):
        pass

    @abstractmethod
    async def subscribe(self, task_spec, listener):
        pass

    @abstractmethod
    async def notify_listeners(self, task_spec, message):
        pass

    @classmethod
    def create_task_id(cls):
        return str(uuid.uuid4()


class RedisTaskDispatcher(TaskDispatcher):
    def __init__(self, channel_name, redis_client):
        super().__init__()
        self.channel_name = channel_name
        self.redis_client = redis_client

    async def dispatch_task(self, command, task_spec):
        task_id = str(uuid.uuid4())

        task_json = json.dumps(
            {"command": command, "task_spec": task_spec, "task_id": task_id}
        )
        await self.redis_client.rpush("task_queue", task_json)

    def subscribe(self, task_spec, listener):
        if listener not in self.listeners[task_spec]:
            self.listeners[task_spec].append(listener)

    async def notify_listeners(self, message):

        task_spec = message["task_spec"]

        listeners = self.listeners[task_spec]
        for listener in listeners:
            await listener(message)

    async def listen_for_task_updates(self):
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:

                data = json.loads(message["data"].decode("utf-8"))

                await self.notify_listeners(data)

    async def start_listening(self):
        self.pubsub = pubsub = await self.redis_client.pubsub()

        await pubsub.subscribe(self.channel_name)
        asyncio.create_task(self.listen_for_task_updates())


class LocalTaskDispatcher(TaskDispatcher):
    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager

    async def dispatch_task(self, command, task_spec):
        task_info = {"command": command, "task_spec": task_spec}
        await self.task_manager.enqueue_task_command(task_info)
        await self.task_manager.subscribe_all(self.notify_listeners)

    async def subscribe(self, task_spec, listener):
        if listener not in self.listeners[task_spec]:
            self.listeners[task_spec].append(listener)

    async def notify_listeners(self, task_spec, message):
        listeners = self.listeners[task_spec]
        for listener in listeners:
            await listener(task_spec, message)
