#!/usr/bin/env python3


class Config:
    STRATEGY_CHANNEL_NAME = "strategy"

    def __init__(self, environment):
        self.environment = environment

        self.redis_url = environment.get("STRATEGY_REDIS_URL", "redis://localhost:6379")

    @property
    def redis_config(self):
        return {
            "strategy": {
                "url": self.redis_url,
                "db": 0,
                "password": None,
                "encoding": "utf-8",
            }
        }
