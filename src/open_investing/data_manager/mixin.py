#!/usr/bin/env python3
from asgiref.sync import sync_to_async
from open_investing.data_manager.const import DataReturnType
from typing import Any
from open_library.pandas.dataframe import read_frame
from django.db.models.query import QuerySet


class ReturnTypeMixin:
    async def handle_return(
        self,
        qs: QuerySet[Any],
        return_type: DataReturnType,
        field_names: list | None = None,
    ):
        if return_type == DataReturnType.Queryset:
            return qs
        elif return_type == DataReturnType.List:
            field_names = field_names or []
            return await sync_to_async(qs.values)(*field_names)
        elif return_type == DataReturnType.Dataframe:
            return await read_frame(qs)

        else:
            raise ValueError("Invalid return_type specified.")
