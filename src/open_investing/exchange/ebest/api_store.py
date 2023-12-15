#!/usr/bin/env python3
from typing import Union, Dict


class EbestApiType:
    Stock = "stock"
    Derivative = "derivative"


class EbestApiStore:
    def __init__(self):
        self._store: Dict[str, "EbestApi"] = {}

    def set(self, exchange_api: "EbestApi", api_type: EbestApiType):
        self._store[api_type] = exchange_api

    def get(self, api_type: EbestApiType = None, **kwargs) -> Union["EbestApi", None]:
        if api_type is None:
            api_type = EbestApiType.Stock
        return self._store.get(api_type)


ebest_api_store = EbestApiStore()
