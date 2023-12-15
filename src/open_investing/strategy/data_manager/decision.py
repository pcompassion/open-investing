#!/usr/bin/env python3


from typing import Dict, Any
from open_investing.order.models.decision import Decision


class DecisionManager:
    async def open_decision(
        self,
        decision: Decision,
        strategy_id: str,
        strategy_name: str,
        decision_type: str,
        decision_params: Dict[str, Any],
        amount: float,
    ):
        await decision.asave(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            decision_type=decision_type,
            decision_params=decision_params,
            amount=amount,
            life_stage=DecisionLifeStage.OPENED,
        )

    async def get_last_decision(
        self,
        strategy_id: str,
    ):
        return (
            await Decision.objects.filter(strategy_id=strategy_id)
            .order_by("created_at")
            .alast()
        )


decision_manager = DecisionManager()
