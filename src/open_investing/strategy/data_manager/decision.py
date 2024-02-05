#!/usr/bin/env python3


from open_library.time.datetime import now_local
from decimal import Decimal
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

    excludes_json = [
        "quantity_multiplier",
        "quantity_order",
        "quantity_exposure",
        "filled_quantity_order",
        "filled_quantity_exposure",
    ]

    async def prepare_decision(self, params: dict, save=True):
        plain = {k: v for k, v in params.items() if k in self.excludes_json}
        params_updated = to_jsonable_python(params, excludes=self.excludes_json) | plain

        decision = Decision(**params_updated)

        if save:
            await self.save(decision, {})

        return decision

    async def save(self, decision, save_params: dict):
        plain = {k: v for k, v in save_params.items() if k in self.excludes_json}

        params = to_jsonable_python(save_params, excludes=self.excludes_json) | plain

        for field, value in params.items():
            setattr(decision, field, value)

        await decision.asave()

    async def make_decision(
        self,
        decision: Decision,
        decision_params: Dict[str, Any],
        quantity_order: Decimal,
        quantity_multiplier: Decimal,
        decision_command_name: str,
    ):
        now = now_local()
        save_params = dict(
            decision_params=decision_params,
            quantity_order=quantity_order,
            quantity_multiplier=quantity_multiplier,
            life_stage=DecisionLifeStage.Decided,
            life_stage_upddated_at=now,
            decision_command_name=decision_command_name,
        )

        await self._save(
            decision,
            save_params=save_params,
        )
        return decision

    async def set_started(self, decision: Decision):
        now = now_local()
        await self._save(
            decision,
            save_params=dict(
                life_stage=DecisionLifeStage.Started, life_stage_updated_at=now
            ),
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
        plain = {k: v for k, v in save_params.items() if k in self.excludes_json}

        params = to_jsonable_python(save_params, excludes=self.excludes_json) | plain

        for field, value in params.items():
            setattr(decision, field, value)
        await decision.asave()
