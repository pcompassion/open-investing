#!/usr/bin/env python3

from open_investing.strategy.const.strategy import StrategyLifeStage
from typing import Dict, Any
from open_investing.locator.service_locator import ServiceKey
from open_investing.strategy.models.strategy import StrategySession
from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint


class StrategySessionDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Strategy.StrategySession"},
    )

    async def ongoing_strategy_sessions(
        self,
        filter_params: dict | None = None,
        return_type: ListDataType = ListDataType.List,
    ) -> ListDataTypeHint:
        filter_params = filter_params or {}

        qs = StrategySession.objects.filter(
            life_stage__in=[
                StrategyLifeStage.Opened,
                StrategyLifeStage.Unstarted,
                StrategyLifeStage.Started,
            ]
        )

        if filter_params:
            qs = qs.filter(**filter_params)

        return await as_list_type(qs, return_type)

    async def prepare_strategy_session(self, params: dict):
        strategy_session = StrategySession(
            **params,
        )

        return await strategy_session.asave()
