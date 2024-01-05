#!/usr/bin/env python3
import uuid
from django.db import models

from open_investing.strategy.const.strategy import StrategyLifeStage


class StrategySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    strategy_name = models.CharField(max_length=128)
    life_stage = models.CharField(max_length=32, default=StrategyLifeStage.Unstarted)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
