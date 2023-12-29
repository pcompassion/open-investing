#!/usr/bin/env python3


from open_investing.const.code_name import FieldName

from open_investing.const.code_name import DerivativeName

from open_investing.security.security_code import DerivativeCode

from open_investing.exchange.ebest.ebestapi import EbestApi
from open_investing.exchange.const.market_type import ApiType
from open_investing.locator.service_locator import ServiceKey
from open_investing.const.code_name import IndexCode


class EbestApiManager:
    service_key = ServiceKey(
        service_type="exchange_api_manager",
        service_name="ebest",
    )

    def __init__(self):
        pass

    def initialize(self, environment):
        EBEST_APP_KEY = environment.get("EBEST-OPEN-API-APP-KEY")
        EBEST_APP_SECRET = environment.get("EBEST-OPEN-API-SECRET-KEY")

        self.stock_api = EbestApi(EBEST_APP_KEY, EBEST_APP_SECRET, env=environment.env)

        EBEST_APP_KEY_DERIVATIVE = environment.get("EBEST-OPEN-API-APP-KEY-DERIVATIVE")
        EBEST_APP_SECRET_DERIVATIVE = environment.get(
            "EBEST-OPEN-API-SECRET-KEY-DERIVATIVE"
        )

        self.derivative_api = EbestApi(
            EBEST_APP_KEY_DERIVATIVE, EBEST_APP_SECRET_DERIVATIVE
        )

    async def get_nearby_mini_future_codes(self, count=2) -> list[DerivativeCode]:
        api = self.stock_api

        api_response = await api.get_market_data(
            "t8435", send_data={FieldName.DERIVATIVE_NAME: DerivativeName.MiniFuture}
        )

        mini_future_codes = [
            DerivativeCode.from_string(e["shcode"], strike_price=e["recprice"])
            for e in api_response.data[:count]
        ]

        return mini_future_codes, api_response

    async def risk_free_rate_market_indicator(self):
        api = self.stock_api

        api_response = await api.get_market_data(
            "t3521", send_data={"kind": "S", "symbol": "KIR@CD91"}
        )
        data = api_response.data

        change = data["change"]

        return change, api_response

    async def vix_market_indicator(self):
        api = self.stock_api

        send_data = {FieldName.INDEX_CODE: IndexCode.Vkospi}
        api_response = await api.get_market_data("t1511", send_data=send_data)
        data = api_response.data

        pricejisu = data["pricejisu"]

        return pricejisu, api_response
