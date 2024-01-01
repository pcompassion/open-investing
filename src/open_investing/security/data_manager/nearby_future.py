#!/usr/bin/env python3
import pandas as pd
import pendulum
from django.db.models import Window, F, Max

from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import NearbyFuture
from open_investing.locator.service_locator import ServiceKey
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

    async def nearby_futures(
        self,
        max_time_diff: timedelta = timedelta(days=5),
        filter_params: dict | None = None,
        return_type: ListDataType = ListDataType.Dataframe,
    ) -> ListDataTypeHint:
        filter_params = filter_params or {}
        now = now_local()

        future_qs = NearbyFuture.objects.annotate(
            recent_at=Window(
                expression=Max("date_at"), partition_by=[F("security_code")]
            )
        ).filter(date_at=F("recent_at"))

        filter_params_updated = dict(date_at__gt=now - max_time_diff) | filter_params

        if filter_params_updated:
            future_qs = future_qs.filter(**filter_params_updated)

        return await as_list_type(future_qs, return_type)
