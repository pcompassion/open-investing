#!/usr/bin/env python3
from typing import Union, Dict

from .ebest.api_store import ebest_api_store
from .ebest.ebestapi import EbestApi
from open_investing.const.const import EXCHANGE


class ExchangeStore:

    name = EXCHANGE

    def __init__(self):

        self.exchange_api_store = {
            EbestApi.name: ebest_api_store,
        }

        self.exchange_store = {
        }


    def get_exchange(self, exchange_name: str, exchange_params: Dict[str, str]):

        exchange_api_store = self.exchange_api_store.get(exchange_name, None)
        if exchange_api_store:
            exchange_api = exchange_api_store.get(**exchange_params, None)
            return exchange_api

        exchange_api = self.exchange_store.get(exchange_name, None)
        return exchange_api


    def set_exchange(self, exchange_name: str, exchange_api: Union[EbestApi, None] = None, exchange_params: Dict[str, str]):

        exchange_api_store = self.exchange_api_store.get(exchange_name, None)

        if exchange_api_store:
            exchange_api = exchange_api_store.set(exchange_api=exchange_api, **exchange_params)

        else:
            self.exchange_store[exchange_name] = exchange_api


exchange_store = ExchangeStore()
