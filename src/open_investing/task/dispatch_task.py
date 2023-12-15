#!/usr/bin/env python3


import redis
import json

redis_client = redis.Redis(
    host="localhost", port=6379, db=0
)  # adjust parameters as needed


def dispatch_task(task_info):
    task_json = json.dumps(task_info)
    redis_client.rpush("task_queue", task_json)  # 'task_queue' is the Redis list name
