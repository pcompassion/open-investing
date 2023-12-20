#!/usr/bin/env python3
from open_investing.task_spec.task_spec import TaskSpec
import json
from open_investing.task.task_manager import TaskManager
import logging

logger = logging.getLogger(__name__)


class RedisTaskReceiver:
    def __init__(self, task_manager: TaskManager, channel_name: str, redis_client):
        self.task_manager = task_manager
        self.channel_name = channel_name
        self.redis_client = redis_client

        self.task_manager.subscribe_all(self.notify_listners)

    async def run(self):
        while True:
            _, raw_json = await self.redis_client.blpop("task_queue")

            data = raw_json.decode("utf-8")

            task_info = json.loads(data)

            logger.info("received task: %s", task_info["task_spec"]["spec_type_name"])

            await self.task_manager.enqueue_task_command(task_info)

    async def notify_listners(self, message):
        task_spec_ = message["task_spec"]

        if isinstance(task_spec_, TaskSpec):
            task_spec = task_spec_.model_dump()
        else:
            task_spec = task_spec_

        message["task_spec"] = task_spec

        await self.redis_client.publish(self.channel_name, json.dumps(message))
