#!/usr/bin/env python3
from django.db.models.functions import Rank

from open_library.time.datetime import now_local
from asgiref.sync import sync_to_async
from open_library.pandas.dataframe import serialize_row
import pandas as pd
import pendulum
from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import Option
from open_library.locator.service_locator import ServiceKey
from django.db.models import Window, F, Max, Min
from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint
from open_library.extension.django.orm import get_model_field_names
from open_library.collections.dict import filter_dict
from open_library.collections.dict import to_jsonable_python


class OptionDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Security.Option"},
    )

    def initialize(self, environment):
        pass

    async def save(self, option_or_id, save_params: dict):
        params = to_jsonable_python(save_params)

        if isinstance(option_or_id, Option):
            option = option_or_id

            for field, value in params.items():
                setattr(option, field, value)

            update_fields = list(params.keys())

            await option.asave(update_fields=update_fields)
        else:
            await Option.objects.filter(id=option_or_id).aupdate(**params)

    async def last(self, **params):
        return await Option.objects.filter(**params).order_by("date_at").alast()

    async def save_options(
        self,
        options_data: ListDataTypeHint,
        extra_data: dict,
        field_names: list[str] = None,
    ):
        extra_data = extra_data or {}

        option_dicts = await as_list_type(options_data, data_type=ListDataType.ListDict)
        field_names = field_names or get_model_field_names(Option)

        option_ids = []

        for option_data in option_dicts:
            option, created = await Option.objects.aget_or_create(
                **filter_dict(option_data, field_names),
                **extra_data,
            )
            option_ids.append(option.id)
            option_data["id"] = option.id

        if isinstance(options_data, pd.DataFrame):
            options_data.loc[:, "id"] = option_ids

        return options_data

    async def recent_options(
        self,
        filter_params: dict | None = None,
        field_names: list | None = None,
        return_type: ListDataType = ListDataType.Dataframe,
        # ):
        # ) -> QuerySet:
    ) -> ListDataTypeHint:
        """
        SELECT *,
        MIN(expire_at) OVER (PARTITION BY security_code) as recent_at,
        RANK() OVER (PARTITION BY security_code ORDER BY expire_at ASC, date_at DESC) as rank
        FROM option
        WHERE expire_at > 'your_now_value'
        HAVING expire_at = recent_at AND rank = 1
        ORDER BY expire_at, date_at;

        """
        # TODO: this is taking too long, too many data
        now = now_local()
        filter_params = filter_params or {}

        filter_params_updated = dict(expire_at__gt=now) | filter_params

        option_qs = (
            Option.objects.filter(**filter_params_updated)
            .annotate(
                recent_at=Window(
                    expression=Min("expire_at"), partition_by=[F("security_code")]
                ),
                rank=Window(
                    expression=Rank(),
                    partition_by=[F("security_code")],
                    order_by=[F("expire_at").asc(), F("date_at").desc()],
                ),
            )
            .filter(expire_at=F("recent_at"), rank=1)
            .order_by("expire_at", "date_at")
        )
        return await as_list_type(option_qs, return_type, field_names)

        # option_qs = Option.objects.filter(**filter_params_updated)

        # option_df_ = await as_list_type(option_qs, return_type, field_names)
        # # Group by 'security_code' and find the index of the row with the minimum 'expire_at'
        # idx = option_df_.groupby("security_code")["expire_at"].idxmin()

        # # Use the indices to filter the DataFrame
        # option_df = option_df_.loc[idx]
        # return option_df
