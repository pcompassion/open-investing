#!/usr/bin/env python3
import redis
from open_investing.event_spec.event_spec import EventSpec
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

        self.task_manager.subscribe_all(self.notify_listeners)

    async def run(self):
        try:
            while True:
                _, raw_json = await self.redis_client.blpop("task_queue")

                try:
                    try:
                        data = raw_json.decode("utf-8")
                    except (UnicodeDecodeError, json.decoder.JSONDecodeError) as e:
                        print(f"Failed to decode JSON: {e}")
                        continue

                    task_info = json.loads(data)

                    logger.info(
                        "received task: %s, command: %s",
                        task_info["task_spec"]["spec_type_name"],
                        task_info["command"],
                    )

                    await self.task_manager.enqueue_task_command(task_info)
                except Exception as general_exception:
                    logger.exception(
                        "Failed to enqueue task command: %s", general_exception
                    )

        except redis.exceptions.ConnectionError as e:
            logger.exception(
                f"Redis connection error: {e}",
            )
            raise e

    async def notify_listeners(self, message):
        event_spec_ = message["event_spec"]

        if isinstance(event_spec_, EventSpec):
            event_spec = event_spec_.model_dump()
        else:
            event_spec = event_spec_

        message_updated = message | {"event_spec": event_spec}

        try:
            await self.redis_client.publish(
                self.channel_name, json.dumps(message_updated)
            )
        except Exception as e:
            pass
