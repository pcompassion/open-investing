#!/usr/bin/env python3

import pendulum
from datetime import timedelta
from open_investing.security.security_code import DerivativeCode
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

    async def save_futures(
        self, futures_df: pd.DataFrame, exchange_data: dict, expire_date
    ):
        exchange_data = exchange_data or {}

        future_ids = []
        for future_data in futures_df.itertuples():
            future, created = await SecurityFuture.objects.aget_or_create(
                price=future_data.price,
                expire_date=expire_date,
                security_code=future_data.security_code,
                date_at=future_data.datetime,
                data=serialize_row(future_data),
                timeframe=timedelta(self.interval_second),
                **exchange_data,
            )
            future_ids.append(future.id)

        futures_df["id"] = future_ids

        return futures_df
