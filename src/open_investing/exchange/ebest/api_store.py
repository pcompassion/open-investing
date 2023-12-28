#!/usr/bin/env python3
from typing import Union, Dict, cast
from enum import Enum
from open_investing.exchange.ebest.ebestapi import EbestApi
from open_investing.exchange.const.market_type import ApiType
from open_investing.exchange.exchange_api import ExchangeApi


class EbestApiStore:
    api_class = EbestApi

    def __init__(self):
        self._store: Dict[str, EbestApi] = {}

    def set(self, exchange_api: ExchangeApi, **kwargs):
        api_type: ApiType = kwargs.pop("api_type", ApiType.Undefined)

        exchange_api = cast(EbestApi, exchange_api)

        self._store[api_type] = exchange_api

    def get(self, **kwargs) -> Union[EbestApi, None]:
        api_type: ApiType = kwargs.pop("api_type", ApiType.Undefined)
        if api_type is None:
            api_type = ApiType.Stock
        return self._store.get(api_type)
