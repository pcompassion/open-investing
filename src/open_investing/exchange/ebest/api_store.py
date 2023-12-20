#!/usr/bin/env python3
from typing import Union, Dict
from enum import Enum
from open_investing.exchange.ebest.ebestapi import EbestApi
from open_investing.exchange.const.market_type import ApiType


class EbestApiStore:
    def __init__(self):
        self._store: Dict[str, "EbestApi"] = {}

    def set(self, exchange_api: "EbestApi", **kwargs):
        api_type: ApiType = kwargs.pop("api_type", ApiType.Undefined)

        self._store[api_type] = exchange_api

    def get(self, **kwargs) -> Union["EbestApi", None]:
        api_type: ApiType = kwargs.pop("api_type", ApiType.Undefined)
        if api_type is None:
            api_type = ApiType.Stock
        return self._store.get(api_type)
