#!/usr/bin/env python3

from typing import Protocol


class StrategySessionManagerProtocol(Protocol):
    async def started_strategy_sessions(
        filter_params: dict | None, return_type: ListDataType
    ) -> ListDataTypeHint:
        ...
