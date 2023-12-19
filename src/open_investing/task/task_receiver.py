#!/usr/bin/env python3
import json
from open_investing.task.task_manager import TaskManager


class RedisTaskReceiver:
    def __init__(self, task_manager: TaskManager, channel_name: str, redis_client):
        self.task_manager = task_manager
        self.channel_name = channel_name
        self.redis_client = redis_client

        self.task_manager.subscribe_all(self.notify_listners)

    async def run(self):
        while True:
            _, raw_data = await self.redis_client.blpop("task_queue")

            data = raw_data.decode("utf-8")

            task_info = json.loads(data)

            await self.task_manager.enqueue_task_command(task_info)

    def notify_listners(self, message):
        await self.redis_client.publish(self.channel_name, message)
