#!/usr/bin/env python3

from open_library.pandas.dataframe import serialize_row
import pandas as pd
import pendulum
from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import Future
from open_investing.locator.service_locator import ServiceKey


class FutureDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Future"},
    )

    def initialize(self, environment):
        pass

    async def last(self, **params):
        return await Future.objects.filter(**params).order_by("date_at").alast()

    async def save_futures(self, futures_df: pd.DataFrame, extra_data: dict):
        extra_data = extra_data or {}

        future_ids = []
        for future_data in futures_df.itertuples():
            future, created = await Future.objects.aget_or_create(
                price=future_data.price,
                security_code=future_data.security_code,
                date_at=future_data.datetime,
                data=serialize_row(future_data),
                **extra_data,
            )
            future_ids.append(future.id)

        futures_df["id"] = future_ids

        return futures_df
