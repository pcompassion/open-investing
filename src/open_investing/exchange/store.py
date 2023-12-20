#!/usr/bin/env python3
from typing import Union, Dict, Any, Optional

from .ebest.api_store import EbestApiStore
from .ebest.ebestapi import EbestApi
from open_investing.const.const import EXCHANGE


class ExchangeStore:
    name = EXCHANGE

    def __init__(self):
        self.exchange_api_store = {
            EbestApi.name: EbestApiStore(),
        }

        self.exchanges = {}

    def get_exchange(self, exchange_name: str, exchange_params: Dict[Any, str]):
        exchange_api_store = self.exchange_api_store.get(exchange_name, None)
        if exchange_api_store:
            exchange_api = exchange_api_store.get(**exchange_params)
            return exchange_api

        exchange_api = self.exchanges.get(exchange_name, None)
        return exchange_api

    def set_exchange(
        self,
        exchange_name: str,
        exchange_api: EbestApi,
        exchange_params: Optional[Dict[str, str]] = None,
    ):
        exchange_api_store = self.exchange_api_store.get(exchange_name, None)

        if exchange_api_store:
            exchange_params = exchange_params or {}
            exchange_api_store.set(exchange_api=exchange_api, **exchange_params)

        else:
            self.exchanges[exchange_name] = exchange_api
