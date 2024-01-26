#!/usr/bin/env python3
import pandas as pd
import pendulum
from django.db.models import Window, F, Max, Min
from asgiref.sync import sync_to_async

from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import NearbyFuture
from open_library.locator.service_locator import ServiceKey
from open_library.time.datetime import now_local
from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint


class NearbyFutureDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Security.NearbyFuture"},
    )

    def initialize(self, environment):
        pass

    async def save_futures(
        self,
        futures_data: ListDataTypeHint,
        extra_data: dict,
    ):
        future_ids = []

        future_dicts = await as_list_type(futures_data, data_type=ListDataType.ListDict)

        for future_data in future_dicts:
            future, created = await NearbyFuture.objects.aget_or_create(
                **future_data,
                **extra_data,
            )
            future_data["id"] = future.id

        if isinstance(futures_data, pd.DataFrame):
            futures_data["id"] = future_ids

        return futures_data

    async def nearby_future(
        self,
        # 0: trade at expire date
        # 1: trade until previous date of expire date
        minimum_days_before_expire: int = 2,
    ):
        now = now_local()
        today = now.date()

        future = today + timedelta(days=minimum_days_before_expire)

        qs = NearbyFuture.objects.filter(expire_at__date__gte=future).order_by(
            "expire_at"
        )

        return await qs.afirst()
