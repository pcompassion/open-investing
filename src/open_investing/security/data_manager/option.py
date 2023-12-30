#!/usr/bin/env python3

from open_library.pandas.dataframe import serialize_row
import pandas as pd
import pendulum
from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import Option
from open_investing.locator.service_locator import ServiceKey


class OptionDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Option"},
    )

    def initialize(self, environment):
        pass

    async def last(self, **params):
        return await Option.objects.filter(**params).order_by("date_at").alast()

    async def save_options(self, options_df: pd.DataFrame, extra_data: dict):
        extra_data = extra_data or {}

        option_ids = []
        for option_data in options_df.itertuples():
            option, created = await Option.objects.aget_or_create(
                price=option_data.price,
                security_code=option_data.security_code,
                strike_price=option_data.strike_price,
                date_at=option_data.datetime,
                data=serialize_row(option_data),
                **extra_data,
            )
            option_ids.append(option.id)

        options_df["id"] = option_ids

        return options_df
