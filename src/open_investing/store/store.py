#!/usr/bin/env python3
from typing import Any, Dict


class Store:
    _store: Dict[str, Any] = {}

    def __init__(self):
        # self._store[exchange_store.name] = exchange_store
        pass

    def get(self, store_name: str):
        return self._store.get(store_name)
