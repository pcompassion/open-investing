#!/usr/bin/env python3


from typing import Dict, Any
from open_investing.strategy.models.decision import Decision
from open_investing.locator.service_locator import ServiceKey
from open_investing.strategy.const.decision import DecisionLifeStage


class DecisionDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Strategy.Decision"},
    )

    async def make_decision(
        self,
        decision: Decision,
        decision_params: Dict[str, Any],
        amount: float,
    ):
        return await self._save(
            decision,
            save_params=dict(
                decision_params=decision_params,
                amount=amount,
                life_stage=DecisionLifeStage.Decided,
            ),
        )

    async def set_started(self, decision: Decision):
        return await self._save(
            decision, save_params=dict(life_stage=DecisionLifeStage.Started)
        )

    async def last(
        self,
        strategy_name: str,
    ):
        return (
            await Decision.objects.filter(strategy_name=strategy_name)
            .order_by("created_at")
            .alast()
        )

    async def _save(
        self,
        decision: Decision,
        save_params: Dict[str, Any],
    ):
        return await decision.asave(
            **save_params,
        )
