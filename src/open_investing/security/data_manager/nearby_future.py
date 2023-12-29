#!/usr/bin/env python3
import pendulum
from datetime import timedelta
from open_investing.security.security_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import NearbyFuture
from open_investing.locator.service_locator import ServiceKey


class NearbyFutureDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "NearbyFuture"},
    )

    def initialize(self, environment):
        pass

    async def create(
        self,
        derivative_codes: list[DerivativeCode],
        exchange_api_code,
        exchange_name,
        timeframe,
    ):
        derivative_code_dicts = [
            instance_to_dict(
                derivative_code,
                fields=[
                    "derivative_type",
                    "expire_date",
                    "strike_price",
                    "future_name",
                ],
            )
            for derivative_code in derivative_codes
        ]

        derivative_code_dicts = sorted(
            derivative_code_dicts, key=lambda x: x["expire_date"]
        )

        NearbyFuture.objects.acreate(
            data=derivative_code_dicts,
            exchange_api_code=exchange_api_code,
            exchange_name=exchange_name,
            timeframe=timeframe,
            date_at=pendulum.now(),
        )

    async def get_nearby_future_codes(
        self, max_time_diff: timedelta
    ) -> list[DerivativeCode]:
        now = pendulum.now()
        nearby_future = (
            await NearbyFuture.objects.filter(date_at__gt=now - max_time_diff)
            .order_by("date_at")
            .alast()
        )

        if nearby_future:
            return [
                DerivativeCode(**future_code_dict)
                for future_code_dict in nearby_future.data
            ]
        return []
