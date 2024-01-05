#!/usr/bin/env python3

from open_investing.strategy.const.strategy import StrategyLifeStage
from typing import Dict, Any
from open_investing.locator.service_locator import ServiceKey
from open_investing.strategy.models.strategy import StrategySession
from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint
from open_library.collections.dict import to_jsonable_python


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
        params_updated = to_jsonable_python(params)

        strategy_session = StrategySession(
            **params_updated,
        )

        return await strategy_session.asave()

    async def get(self, filter_params: dict | None):
        filter_params = filter_params or {}

        filter_params_updated = to_jsonable_python(filter_params)

        return await StrategySession.objects.filter(**filter_params_updated).afirst()
