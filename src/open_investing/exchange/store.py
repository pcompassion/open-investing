#!/usr/bin/env python3
from typing import Union, Dict, Any, Optional, cast

from .ebest.api_store import EbestApiStore
from .ebest.ebestapi import EbestApi
from open_investing.const.const import EXCHANGE
from open_investing.exchange.exchange_api import ExchangeApi


class ExchangeStore:
    name = EXCHANGE

    def __init__(self):
        self.exchange_api_stores = {
            EbestApi.name: EbestApiStore(),
        }

        self.exchanges = {}

    def get_exchange(
        self, exchange_name: str, exchange_params: Dict[Any, str]
    ) -> ExchangeApi | None:
        exchange_api_store = self.exchange_api_stores.get(exchange_name, None)
        if exchange_api_store:
            exchange_api = exchange_api_store.get(**exchange_params)
            return exchange_api

        exchange_api = self.exchanges.get(exchange_name, None)
        return exchange_api

    def set_exchange(
        self,
        exchange_name: str,
        exchange_api: ExchangeApi,
        exchange_params: Optional[Dict[str, str]] = None,
    ):
        exchange_api_store = self.exchange_api_stores.get(exchange_name, None)

        if exchange_api_store:
            exchange_params = exchange_params or {}
            exchange_api_store.set(exchange_api=exchange_api, **exchange_params)

        else:
            self.exchanges[exchange_name] = exchange_api
