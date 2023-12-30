#!/usr/bin/env python3

from open_library.time.datetime import determine_datetime
from open_investing.exchange.ebest.api_field import EbestApiField
import pandas as pd
from open_investing.exchange.ebest.api_data import EbestApiData
import pendulum

from open_investing.const.code_name import FieldName

from open_investing.const.code_name import DerivativeName

from open_investing.security.security_code import DerivativeCode

from open_investing.exchange.ebest.ebestapi import EbestApi
from open_investing.exchange.const.market_type import ApiType
from open_investing.locator.service_locator import ServiceKey
from open_investing.const.code_name import IndexCode

DEFAULT_TIME_FORMAT = "%H%M%S"


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

    async def future_prices(
        self,
        future_code: DerivativeCode,
        interval_second: int,
        future_data_manager=None,
        save=True,
    ):
        """
        fetch future prices
        if now is in day market, fetch day price
        otherwise fetch night price
        """
        api = self.stock_api

        security_code = future_code.name
        base_datetime = pendulum.now()

        future_last = None

        num_intervals = 900  # MAX_DATAPOINTS
        start_at = None

        day_market_tr = "t2209"
        night_market_tr = "t8429"

        if future_data_manager:
            future_last = await future_data_manager.last(security_code=security_code)

            start_at = pendulum.instance(future_last.date_at)
            num_intervals = (
                pendulum.now().diff(start_at).in_seconds() // interval_second + 10
            )

        time_interval_day_market = EbestApiData.get(day_market_tr, "time_interval")
        time_interval_night_market = EbestApiData.get(day_market_tr, "time_interval")

        send_data = EbestApiField.get_interval(interval_second=interval_second)

        send_data.update(
            {"cnt": num_intervals, FieldName.SECURITY_CODE: future_code.name}
        )

        api_response = None
        if (
            time_interval_day_market[0]
            <= base_datetime.time()
            <= time_interval_day_market[1]
        ):
            api_response = await api.get_market_data(day_market_tr, send_data=send_data)
        elif (
            time_interval_night_market[0]
            <= base_datetime.time()
            <= time_interval_night_market[1]
        ):
            api_response = await api.get_market_data(
                night_market_tr, send_data=send_data
            )

        if api_response is None:
            return pd.DataFrame()

        futures_df = pd.DataFrame(api_response.data)
        if not len(futures_df):
            return futures_df

        futures_df["datetime"] = futures_df["chetime"].apply(
            lambda x: determine_datetime(x, base_datetime, DEFAULT_TIME_FORMAT)
        )

        if start_at:
            futures_df = futures_df.loc[futures_df["datetime"] > start_at]

        futures_df["security_code"] = security_code

        if save:
            if not future_data_manager:
                raise ValueError("future_data_manager is None")

            futures_df = await future_data_manager.save_futures(futures_df)

        return futures_df
