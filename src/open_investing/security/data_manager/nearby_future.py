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

    async def nearby_futures(
        self,
        max_time_diff: timedelta = timedelta(days=5),
        filter_params: dict | None = None,
        return_type: ListDataType = ListDataType.Dataframe,
    ) -> ListDataTypeHint:
        # TODO: don't need this logic
        filter_params = filter_params or {}
        now = now_local()

        future_qs = (
            NearbyFuture.objects.filter(expire_at__gt=now)
            .annotate(
                recent_at=Window(
                    expression=Min("expire_at"), partition_by=[F("security_code")]
                )
            )
            .filter(expire_at=F("recent_at"))
            .order_by("expire_at")
        )

        # filter_params_updated = dict(expire_at__gt=now) | filter_params

        # if filter_params_updated:
        #     future_qs = future_qs.filter(**filter_params_updated)

        return await as_list_type(future_qs, return_type)

    async def nearby_expires(
        self,
        filter_params: dict | None = None,
    ):
        filter_params = filter_params or {}
        now = now_local()

        qs = (
            NearbyFuture.objects.filter(expire_at__gt=now)
            .values_list("expire_at", flat=True)
            .order_by("expire_at")
            .distinct()
        )

        # filter_params_updated = dict(expire_at__gt=now) | filter_params

        # if filter_params_updated:
        #     future_qs = future_qs.filter(**filter_params_updated)

        return await sync_to_async(list)(qs)
