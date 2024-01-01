#!/usr/bin/env python3

import pandas as pd
from typing import Any, Union
from enum import Enum

from django.db.models.query import QuerySet


class DataReturnType(str, Enum):
    Dataframe = "dataframe"
    List = "list"


_DataReturnTypeHint = Union[list[Any], pd.DataFrame]

DataReturnTypeHint = _DataReturnTypeHint | dict[str, _DataReturnTypeHint]
