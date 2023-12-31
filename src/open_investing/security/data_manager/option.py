#!/usr/bin/env python3

from asgiref.sync import sync_to_async
from open_library.pandas.dataframe import serialize_row
import pandas as pd
import pendulum
from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import Option
from open_investing.locator.service_locator import ServiceKey
from django.db.models import Window, F, Max
from open_investing.data_manager.mixin import ReturnTypeMixin
from open_investing.data_manager.const import DataReturnType, ReturnTypeHint


class OptionDataManager(ReturnTypeMixin):
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Security.Option"},
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
                date_at=option_data.date_at,
                data=serialize_row(option_data),
                **extra_data,
            )
            option_ids.append(option.id)

        options_df["id"] = option_ids

        return options_df

    async def recent_options(
        self,
        filter_params: dict | None = None,
        field_names: list | None = None,
        return_type: DataReturnType = DataReturnType.Dataframe,
        # ):
        # ) -> QuerySet:
    ) -> ReturnTypeHint:
        """
        SELECT *, MAX(date_at) OVER (PARTITION BY security_code) as recent_at
        FROM option_table
        WHERE date_at = recent_at;
        """

        option_qs = Option.objects.annotate(
            recent_at=Window(
                expression=Max("date_at"), partition_by=[F("security_code")]
            )
        ).filter(date_at=F("recent_at"))

        if filter_params:
            option_qs = option_qs.filter(**filter_params)

        # return option_qs
        # return await sync_to_async(option_qs.values)(*field_names)
        return await self.handle_return(option_qs, return_type, field_names)
