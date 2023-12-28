#!/usr/bin/env python3

from open_investing.indicator.models import MarketIndicator
import pendulum
from datetime import timedelta


class MarketIndicatorManager:
    async def get(self, name: str, max_time_diff: timedelta) -> MarketIndicator:
        now = pendulum.now()
        return (
            await MarketIndicator.objects.filter(
                name=name, date_at__gt=now - max_time_diff
            )
            .order_by("date_at")
            .alast()
        )


market_indicator_manager = MarketIndicatorManager()
