#!/usr/bin/env python3

DEFAULT_TIME_FORMAT = "HHmmss"


STRATEGY_CHANNEL_NAME = "strategy"

redis_config = {
    "strategy": {
        "url": "redis://localhost:6379",
        # Can be a tuple or a string
        "db": 0,
        "password": None,
        "encoding": "utf-8",
    }
}
