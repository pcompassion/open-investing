#!/usr/bin/env python3

from asgiref.sync import sync_to_async
from open_library.pandas.dataframe import serialize_row
import pandas as pd
import pendulum
from datetime import timedelta
from open_investing.security.derivative_code import DerivativeCode
from open_library.collections.dict import instance_to_dict

from open_investing.security.models import Option
from open_library.locator.service_locator import ServiceKey
from django.db.models import Window, F, Max
from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint
from open_library.extension.django.orm import get_model_field_names
from open_library.collections.dict import filter_dict


class OptionDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Security.Option"},
    )

    def initialize(self, environment):
        pass

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

        return await as_list_type(option_qs, return_type, field_names)
