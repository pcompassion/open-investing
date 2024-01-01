#!/usr/bin/env python3
import pandas as pd
from asgiref.sync import sync_to_async
from open_investing.data_manager.const import DataReturnType
from typing import Any
from open_library.pandas.dataframe import read_frame
from django.db.models.query import QuerySet
from open_investing.data_manager.const import InputDataTypeHint, DataReturnTypeHint


class ReturnDataMixin:
    async def handle_return(
        self,
        data: DataReturnTypeHint,
        return_type: DataReturnType,
        field_names: list | None = None,
    ):
        if return_type == DataReturnType.Queryset:
            assert isinstance(data, QuerySet[Any]), "data is not QuerySet"
            return data
        elif return_type == DataReturnType.List:
            field_names = field_names or []

            if isinstance(data, QuerySet[Any]):
                qs = data
                return await sync_to_async(qs.values)(*field_names)
            elif isinstance(data, list):
                return data
        elif return_type == DataReturnType.Dataframe:
            return await read_frame(data)

        else:
            raise ValueError("Invalid return_type specified.")


class InputDataMixin:
    def as_list_of_dict(
        self,
        data: InputDataTypeHint,
    ) -> list[dict]:
        """
        Prepares data for saving to a model. Converts a DataFrame to a list of dictionaries if necessary.

        :param data: The data to prepare. Can be either a Pandas DataFrame or a list of dictionaries.
        :return: A list of dictionaries representing the data.
        """
        if isinstance(data, pd.DataFrame):
            # Convert the entire DataFrame to a list of dictionaries at once
            data_dicts = data.to_dict("records")
        elif isinstance(data, list) and any(isinstance(item, dict) for item in data):
            data_dicts = data
        else:
            raise ValueError(
                "Data must be a list of dictionaries or a pandas DataFrame."
            )

        return data_dicts
