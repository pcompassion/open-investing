#!/usr/bin/env python3


from open_library.data.conversion import ListDataType, ListDataTypeHint, as_list_type
from typing import Dict, Any
from open_investing.strategy.models.decision import Decision
from open_library.locator.service_locator import ServiceKey
from open_investing.strategy.const.decision import DecisionLifeStage
from open_library.collections.dict import to_jsonable_python


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
        quantity: float,
    ):
        await self._save(
            decision,
            save_params=dict(
                decision_params=decision_params,
                quantity=quantity,
                life_stage=DecisionLifeStage.Decided,
            ),
        )
        return decision

    async def set_started(self, decision: Decision):
        await self._save(
            decision, save_params=dict(life_stage=DecisionLifeStage.Started)
        )
        return decision

    async def last(
        self,
        strategy_name: str,
    ):
        return (
            await Decision.objects.filter(strategy_name=strategy_name)
            .order_by("created_at")
            .alast()
        )

    async def get(self, filter_params: dict):
        return await Decision.objects.aget(**filter_params)

    async def ongoing_decisions(
        self,
        strategy_session_id: str,
        field_names: list | None = None,
        return_type: ListDataType = ListDataType.List,
    ) -> ListDataTypeHint:
        filter_params = dict(
            life_stage__in=[
                DecisionLifeStage.Decided,
                DecisionLifeStage.Started,
                DecisionLifeStage.Opened,
            ]
        )

        qs = Decision.objects.filter(
            strategy_session_id=strategy_session_id, **filter_params
        ).order_by("created_at")

        return await as_list_type(qs, return_type, field_names)

    async def _save(
        self,
        decision: Decision,
        save_params: Dict[str, Any],
    ):
        params = to_jsonable_python(save_params)
        for field, value in params.items():
            setattr(decision, field, value)
        await decision.asave()
