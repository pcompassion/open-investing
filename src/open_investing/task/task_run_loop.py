#!/usr/bin/env python3

import asyncio
import json

from open_investing.task.task_manager import TaskManager
import redis

redis_client = redis.Redis(
    host="localhost", port=6379, db=0
)  # use the same parameters as your Django server


async def main():
    task_manager = TaskManager()
    asyncio.create_task(task_manager.run())  # Start the task manager's run loop

    while True:
        _, task_json = redis_client.blpop("task_queue")
        task_info = json.loads(task_json)
        await task_manager.enqueue_task_command(task_info)


if __name__ == "__main__":
    asyncio.run(main())
