#!/usr/bin/env python3

from datetime import timedelta
from typing import Tuple
from open_library.time.datetime import determine_datetime, now_local
from open_investing.exchange.ebest.api_field import EbestApiField
import pandas as pd
from open_investing.exchange.ebest.api_data import EbestApiData
import pendulum
from open_library.api_client.api_client import ApiResponse
from open_investing.const.code_name import DerivativeType, FieldName

from open_investing.const.code_name import DerivativeType

from open_investing.security.derivative_code import DerivativeCode

from open_investing.exchange.ebest.ebestapi import EbestApi
from open_investing.exchange.const.market_type import ApiType
from open_investing.locator.service_locator import ServiceKey
from open_investing.const.code_name import IndexCode
from open_investing.security.derivative_code import DerivativeCode, DerivativeTypeCode

from open_investing.config.base import DEFAULT_TIME_FORMAT
from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint
from open_investing.exchange.ebest.mixin.order import OrderMixin
from open_library.observe.pubsub_broker import PubsubBroker


class EbestApiManager(OrderMixin):
    service_key = ServiceKey(
        service_type="exchange_api_manager",
        service_name="ebest",
    )

    def __init__(self):
        pass

    async def initialize(self, environment):
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

        await self.stock_api.subscribe(
            tr_type="1", tr_code="SC1", tr_key="", handler=self.stock_order_listener
        )

        await self._api.subscribe(
            tr_type="1",
            tr_code="C01",
            tr_key="",
            handler=self.derivative_order_listener,
        )
        self.order_exchange_event_broker: PubsubBroker | None = None

    def set_order_exchange_event_broker(self, order_exchange_event_broker):
        self.order_exchange_event_broker = order_exchange_event_broker

    async def nearby_mini_futures(
        self,
        count=2,
        data_manager=None,
        save=True,
        return_type: ListDataType = ListDataType.Dataframe,
    ) -> Tuple[ListDataTypeHint, ApiResponse]:
        api = self.stock_api

        api_code = "t8435"

        api_response = await api.get_market_data(
            api_code, send_data={FieldName.DERIVATIVE_NAME: DerivativeType.MiniFuture}
        )

        mini_future_codes = [
            DerivativeCode.from_string(e["shcode"], price=e["recprice"])
            for e in api_response.data[:count]
        ]
        print("mini_future_codes", mini_future_codes)

        mini_future_codes = sorted(mini_future_codes, key=lambda x: x.expire_at)

        mini_futures_data = [
            derivative_code.to_dict() for derivative_code in mini_future_codes
        ]

        if data_manager and save:
            extra_data = dict(
                date_at=now_local(),
                exchange_name=api.name,
                exchange_api_code=api_code,
                timeframe=timedelta(hours=12),
            )

            mini_futures_data = await data_manager.save_futures(
                mini_futures_data, extra_data=extra_data
            )

        mini_futures_data = await as_list_type(mini_futures_data, return_type)

        return mini_futures_data, api_response

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
        future_data,
        interval_second: int,
        future_data_manager=None,
        save=True,
        return_type: ListDataType = ListDataType.Dataframe,
    ):
        """
        fetch future prices
        if now is in day market, fetch day price
        otherwise fetch night price
        """
        api = self.stock_api

        security_code = future_data.security_code
        base_datetime = pendulum.now()

        future_last = None

        MAX_DATAPOINTS = 900
        num_intervals = MAX_DATAPOINTS  # MAX_DATAPOINTS
        start_at = None

        day_market_tr = "t2209"
        night_market_tr = "t8429"

        time_interval_day_market = EbestApiData.get(day_market_tr, "time_interval")
        time_interval_night_market = EbestApiData.get(day_market_tr, "time_interval")

        send_data = EbestApiField.get_interval(interval_second=interval_second)

        fields = ["expire_at", "derivative_type"]
        mf_dict = {field: getattr(future_data, field) for field in fields}
        mf_code = DerivativeCode(**mf_dict, price=future_data.price)

        tr_code = None
        if (
            time_interval_day_market[0]
            <= base_datetime.time()
            <= time_interval_day_market[1]
        ):
            tr_code = day_market_tr

        elif (
            time_interval_night_market[0]
            <= base_datetime.time()
            <= time_interval_night_market[1]
        ):
            tr_code = night_market_tr

        if tr_code is None:
            #     return pd.DataFrame()
            tr_code = day_market_tr

        if future_data_manager:
            future_last = await future_data_manager.last(
                filter_params=dict(
                    security_code=security_code, exchange_api_code=tr_code
                )
            )

            if future_last:
                start_at = pendulum.instance(future_last.date_at)
                num_intervals = (
                    pendulum.now().diff(start_at).in_seconds() // interval_second + 10
                )
                num_intervals = min(num_intervals, MAX_DATAPOINTS)

        send_data.update(
            {"cnt": num_intervals, FieldName.SECURITY_CODE: mf_code.security_code}
        )
        api_response = await api.get_market_data(tr_code, send_data=send_data)

        if api_response is None:
            return await as_list_type([], return_type), api_response

        futures_df = pd.DataFrame(api_response.data)
        if not len(futures_df):
            return await as_list_type([], return_type), api_response

        futures_df["date_at"] = futures_df["chetime"].apply(
            lambda x: determine_datetime(x, base_datetime, DEFAULT_TIME_FORMAT)
        )

        if start_at:
            futures_df = futures_df.loc[futures_df["date_at"] > start_at]

        futures_df["security_code"] = security_code
        futures_df["expire_at"] = future_data.expire_at

        futures_df = futures_df[["security_code", "expire_at", "date_at", "price"]]

        if save:
            if not future_data_manager:
                raise ValueError("future_data_manager is None")

            extra_data = dict(
                exchange_name=api.name,
                exchange_api_code=tr_code,
                timeframe=timedelta(interval_second),
            )
            futures_df = await future_data_manager.save_futures(
                futures_df, extra_data=extra_data
            )

        result = await as_list_type(futures_df, return_type)

        return result, api_response

    async def option_list(
        self,
        return_type: ListDataType = ListDataType.Dataframe,
    ):
        api = self.stock_api
        api_response = await api.get_market_data("t8433")

        if api_response is None:
            return pd.DataFrame(), api_response

        df = pd.DataFrame(api_response.data)

        valid_codes = {code.value for code in DerivativeTypeCode}
        mask = df["shcode"].str.startswith(tuple(valid_codes), na=False)
        df = df[mask]

        field_names = [
            "name",
            "strike_price",
            "expire_at",
            "security_code",
            "derivative_type",
        ]

        df[field_names] = df["shcode"].apply(
            lambda x: DerivativeCode.get_fields(x, field_names)
        )
        result = await as_list_type(df, return_type)

        return result, api_response

    async def option_prices(
        self,
        option_data,
        interval_second: int,
        option_data_manager=None,
        save=True,
        return_type: ListDataType = ListDataType.Dataframe,
    ):
        """
        fetch option prices
        if now is in day market, fetch day price
        otherwise fetch night price
        """
        api = self.stock_api

        security_code = option_data.security_code
        base_datetime = pendulum.now()

        option_last = None

        MAX_DATAPOINTS = 900
        num_intervals = MAX_DATAPOINTS  # MAX_DATAPOINTS
        start_at = None

        day_market_tr = "t2209"
        night_market_tr = "t8429"

        time_interval_day_market = EbestApiData.get(day_market_tr, "time_interval")
        time_interval_night_market = EbestApiData.get(day_market_tr, "time_interval")

        tr_code = None
        if (
            time_interval_day_market[0]
            <= base_datetime.time()
            <= time_interval_day_market[1]
        ):
            tr_code = day_market_tr

        elif (
            time_interval_night_market[0]
            <= base_datetime.time()
            <= time_interval_night_market[1]
        ):
            tr_code = night_market_tr

        if tr_code is None:
            # return pd.DataFrame()
            tr_code = day_market_tr

        if option_data_manager:
            option_last = await option_data_manager.last(security_code=security_code)

            if option_last:
                start_at = pendulum.instance(option_last.date_at)
                num_intervals = (
                    pendulum.now().diff(start_at).in_seconds() // interval_second + 10
                )
                num_intervals = min(num_intervals, MAX_DATAPOINTS)

        send_data = EbestApiField.get_interval(interval_second=interval_second)

        send_data.update(
            {"cnt": num_intervals, FieldName.SECURITY_CODE: option_data.security_code}
        )

        api_response = await api.get_market_data(tr_code, send_data=send_data)

        if api_response is None:
            return await as_list_type([], return_type), api_response

        options_df = pd.DataFrame(api_response.data)
        if not len(options_df):
            return await as_list_type([], return_type), api_response

        options_df["date_at"] = options_df["chetime"].apply(
            lambda x: determine_datetime(x, base_datetime, DEFAULT_TIME_FORMAT)
        )

        if start_at:
            options_df = options_df.loc[options_df["date_at"] > start_at]

        options_df["expire_at"] = option_data.expire_at

        options_df = options_df[["date_at", "price"]]

        if save:
            if not option_data_manager:
                raise ValueError("option_data_manager is None")

            extra_data = dict(
                exchange_name=api.name,
                exchange_api_code=tr_code,
                strike_price=option_data.strike_price,
                security_code=security_code,
                derivative_type=option_data.derivative_type,
                timeframe=timedelta(interval_second),
            )
            options_df = await option_data_manager.save_options(
                options_df, extra_data=extra_data
            )

        result = await as_list_type(options_df, return_type)

        return result, api_response
