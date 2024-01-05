#!/usr/bin/env python3

from typing import Protocol
from typing import Dict, Any
from open_investing.strategy.models.decision import Decision


from typing import Protocol


class DecisionDataManagerProtocol(Protocol):
    async def make_decision(
        self, decision: Decision, decision_params: Dict[str, Any], quantity: float
    ) -> Any:
        ...

    async def set_started(self, decision: Decision) -> Any:
        ...

    async def last(self, strategy_name: str) -> Any:
        ...

    async def _save(self, decision: Decision, save_params: Dict[str, Any]) -> Any:
        ...
