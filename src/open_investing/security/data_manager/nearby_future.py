#!/usr/bin/env python3
import pendulum
from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import NearbyFuture
from open_investing.locator.service_locator import ServiceKey
from open_library.time.datetime import now_local


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
        extra_data: dict,
    ):
        derivative_code_dicts = [
            instance_to_dict(
                derivative_code,
                fields=[
                    "derivative_type",
                    "expire_date_str",
                    "strike_price",
                    "name",
                    "year",
                    "month",
                ],
            )
            for derivative_code in derivative_codes
        ]

        derivative_code_dicts = sorted(
            derivative_code_dicts, key=lambda x: x["expire_date_str"]
        )

        await NearbyFuture.objects.acreate(
            data=derivative_code_dicts,
            date_at=now_local(),
            **extra_data,
        )

    async def nearby_future_codes(
        self, max_time_diff: timedelta = timedelta(days=5)
    ) -> list[DerivativeCode]:
        now = now_local()
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
