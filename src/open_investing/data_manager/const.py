#!/usr/bin/env python3
import pandas as pd
from typing import Any, Union
from enum import Enum

from django.db.models.query import QuerySet


class DataReturnType(str, Enum):
    Dataframe = "dataframe"
    Queryset = "queryset"
    List = "list"


ReturnTypeHint = Union[QuerySet[Any], list[Any], pd.DataFrame]
