#!/usr/bin/env python3
from typing import Any, Dict

from open_investing.exchange.store import exchange_store


class Store:
    _store: Dict[str, Any] = {}

    def __init__(self):
        self._store[exchange_store.name] = exchange_store


store = Store()
