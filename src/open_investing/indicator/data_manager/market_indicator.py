#!/usr/bin/env python3

from open_library.time.datetime import now_local
from open_investing.indicator.models import MarketIndicator
import pendulum
from datetime import timedelta
from open_library.locator.service_locator import ServiceKey


class MarketIndicatorDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "MarketIndicator"},
    )

    def initialize(self, environment):
        pass

    async def get(self, name: str, max_time_diff: timedelta = None) -> MarketIndicator:
        filter_kwargs = {
            "name": name,
        }

        if max_time_diff:
            now = now_local()
            filter_kwargs["date_at__gt"] = now - max_time_diff

        return (
            await MarketIndicator.objects.filter(**filter_kwargs)
            .order_by("date_at")
            .alast()
        )
