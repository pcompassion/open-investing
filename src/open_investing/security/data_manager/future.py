#!/usr/bin/env python3

from open_library.pandas.dataframe import serialize_row
import pandas as pd
import pendulum
from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import Future
from open_investing.locator.service_locator import ServiceKey
from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint


class FutureDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Security.Future"},
    )

    def initialize(self, environment):
        pass

    async def last(self, filter_params: dict | None = None):
        return await Future.objects.filter(**filter_params).order_by("date_at").alast()

    async def save_futures(self, futures_data: ListDataTypeHint, extra_data: dict):
        extra_data = extra_data or {}

        future_dicts = await as_list_type(futures_data, data_type=ListDataType.ListDict)

        future_ids = []
        for future_data in future_dicts:
            future, created = await Future.objects.aget_or_create(
                **future_data,
                **extra_data,
            )
            future_ids.append(future.id)
            future_data["id"] = future.id

        if isinstance(futures_data, pd.DataFrame):
            futures_data["id"] = future_ids

        return futures_data
