#!/usr/bin/env python3

import datetime
import time
from decimal import Decimal
from open_library.observe.listener_spec import ListenerSpec
from open_investing.event_spec.event_spec import QuoteEventSpec
from open_investing.exchange.const.market import MarketType

from open_investing.exchange.const.market import MarketStatus

from datetime import timedelta
from typing import Any, Tuple
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
from open_investing.exchange.const.market import ApiType
from open_library.locator.service_locator import ServiceKey
from open_investing.const.code_name import IndexCode
from open_investing.security.derivative_code import DerivativeCode, DerivativeTypeCode

from open_library.data.conversion import as_list_type, ListDataType, ListDataTypeHint
from open_investing.exchange.ebest.mixin.order import OrderMixin
from open_library.observe.pubsub_broker import PubsubBroker
import logging
from open_library.time.datetime import combine, time_from_format

from open_investing.security.quote import Quote
from open_library.observe.subscription_manager import SubscriptionManager
from open_library.logging.logging_filter import IntervalLoggingFilter
from open_investing.price.money import Money

logger = logging.getLogger(__name__)

quote_logger = logging.getLogger("quote")
interval_filter = IntervalLoggingFilter(2)  # Log once every 60 seconds
quote_logger.addFilter(interval_filter)


class EbestApiManager(OrderMixin):
    service_key = ServiceKey(
        service_type="exchange_api_manager",
        service_name="ebest",
    )
    name = EbestApi.name
    DEFAULT_TIME_FORMAT = "HHmmss"

    def __init__(self):
        self.order_event_broker: PubsubBroker | None = None
        self.order_data_manager = None
        self.subscription_manager = SubscriptionManager()
        self.running_tasks = []
        self._market_status = MarketStatus.Undefined
        self._market_status_updated_at = None

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

        await self.subscribe_market_status()

    async def subscribe_stock_order(self):
        await self.stock_api.subscribe(
            tr_type="1", tr_code="SC1", tr_key="", handler=self.stock_order_listener
        )

    async def subscribe_derivative_order(self):
        await self.derivative_api.subscribe(
            tr_type="1",
            tr_code="C01",
            tr_key="",
            handler=self.derivative_order_listener,
        )

    async def subscribe_market_status(self):
        await self.stock_api.subscribe(
            tr_type="3", tr_code="JIF", tr_key="0", handler=self.market_status_listener
        )

    async def get_market_data(
        self,
        tr_code: str,
        send_data: dict[Any, Any] | None = None,
        headers: dict[str, Any] | None = None,
    ):
        api = self.stock_api

        return await api.get_market_data(tr_code, send_data=send_data, headers=headers)

    def set_order_event_broker(self, order_event_broker):
        self.order_event_broker = order_event_broker

    def set_order_data_manager(self, order_data_manager):
        self.order_data_manager = order_data_manager

    async def nearby_mini_futures(
        self,
        count=2,
        return_type: ListDataType = ListDataType.Dataframe,
    ) -> Tuple[ListDataTypeHint, ApiResponse]:
        api = self.stock_api

        api_code = None
        market_type = self.open_market_type()
        if market_type == MarketType.FutureOptionDay:
            api_code = "t8435"
        elif market_type == MarketType.FutureOptionNight:
            api_code = "t8437"
        else:
            return [], None

        api_response = await api.get_market_data(
            api_code, send_data={FieldName.DERIVATIVE_NAME: DerivativeType.MiniFuture}
        )

        mini_future_codes = [
            DerivativeCode.from_string(
                e["shcode"], price=Money(amount=0, currency="KRW")  # price not relavant
            )
            for e in api_response.data[:count]
        ]

        mini_future_codes = sorted(mini_future_codes, key=lambda x: x.expire_at)

        mini_futures_data = [
            derivative_code.to_dict() for derivative_code in mini_future_codes
        ]

        mini_futures_data = await as_list_type(mini_futures_data, return_type)

        return mini_futures_data, api_response

    async def risk_free_rate_market_indicator(self):
        api = self.stock_api

        api_response = await api.get_market_data(
            "t3521", send_data={"kind": "S", "symbol": "KIR@CD91"}
        )
        data = api_response.data

        value = data["close"]

        return value, api_response

    async def vix_market_indicator(self):
        api = self.stock_api

        send_data = {FieldName.INDEX_CODE: IndexCode.Vkospi}
        api_response = await api.get_market_data("t1511", send_data=send_data)
        data = api_response.data

        pricejisu = data["pricejisu"]

        return pricejisu, api_response

    async def future_price(
        self,
        security_code: str,
    ):
        api = self.stock_api

        api_code = None

        market_type = self.open_market_type()
        if market_type == MarketType.FutureOptionDay:
            api_code = "t2101"
        elif market_type == MarketType.FutureOptionNight:
            api_code = "t2830"
        else:
            return [], None

        send_data = {
            FieldName.SECURITY_CODE: security_code,
        }
        api_response = await api.get_market_data(api_code, send_data=send_data)
        # return pd.DataFrame(), api_response

        if api_response is None or not api_response.success:
            logger.warn(f"api error while fetching future price")
            return pd.DataFrame(), api_response
        # logger.info(f"api response raw_data {api_response.raw_data} ")

        price = Money(amount=api_response.data["price"], currency="KRW")

        return price, api_response

    async def option_list(
        self,
        expire_at: datetime.datetime,
        return_type: ListDataType = ListDataType.Dataframe,
    ):
        api = self.stock_api
        tr_code = None
        market_type = self.open_market_type()
        if market_type == MarketType.FutureOptionDay:
            tr_code = "t2301"
        elif market_type == MarketType.FutureOptionNight:
            tr_code = "t2835"
        else:
            return [], None

        yyyymm = expire_at.strftime("%Y%m")
        send_data = {"yyyymm": yyyymm}
        api_response = await api.get_market_data(tr_code, send_data=send_data)

        if api_response is None or not api_response.success:
            return pd.DataFrame(), api_response

        data = api_response.data + api_response.raw_data[f"{tr_code}OutBlock2"]
        df = pd.DataFrame(data)

        df.rename(columns={"price": "price_amount"}, inplace=True)
        df["price"] = df["price_amount"].apply(
            lambda x: Money(amount=x, currency="KRW")
        )

        valid_codes = {code.value for code in DerivativeTypeCode}
        mask = df["optcode"].str.startswith(tuple(valid_codes), na=False)
        df = df[mask]

        infered_field_names = [
            "strike_price",
            "expire_at",
            "security_code",
            "derivative_type",
        ]

        df[infered_field_names] = df["optcode"].apply(
            lambda x: DerivativeCode.get_fields(x, infered_field_names)
        )

        df["strike_price_amount"] = df["strike_price"].apply(lambda x: x.amount)
        df["currency"] = df["strike_price"].apply(lambda x: x.currency)

        mask = df["derivative_type"].isin([DerivativeType.Call, DerivativeType.Put])
        df = df[mask]

        result = await as_list_type(df, return_type)

        return result, api_response

    async def subscribe_quote(
        self, event_spec: QuoteEventSpec, listener_spec: ListenerSpec
    ):
        security_code = event_spec.security_code
        derivative_code = DerivativeCode.from_string(security_code)

        api = self.stock_api

        tr_code = None

        match derivative_code.derivative_type:
            case DerivativeType.Future | DerivativeType.MiniFuture:
                tr_code = "FH0"

            case DerivativeType.Put | DerivativeType.Call:
                tr_code = "OH0"
            case _:
                pass

        self.subscription_manager.subscribe(event_spec, listener_spec)

        await api.subscribe(
            tr_type="3",
            tr_code=tr_code,
            tr_key=security_code,
            handler=self.quote_listener,
        )

    async def quote_listener(self, message):
        quote_logger.info(f"quote_listener {message['header']}")

        security_code = message["header"]["tr_key"]
        tr_code = message["header"]["tr_cd"]

        data = message["body"]

        time = time_from_format(data["hotime"], time_format=self.DEFAULT_TIME_FORMAT)
        date_at = combine(now_local().date(), time)

        data["date_at"] = date_at

        data = EbestApiField.get_response_data(tr_code=tr_code, **data)

        for k, v in data.items():
            if k in Quote.model_fields and Quote.model_fields[k].annotation == Money:
                data[k] = Money(amount=Decimal(v), currency="KRW")

        quote_event_spec = QuoteEventSpec(security_code=security_code)
        quote = Quote(**data)

        event_info = dict(event_spec=quote_event_spec, data=quote)

        await self.subscription_manager.publish(event_info)

    async def news_listener(self, message):
        logger.info(f"news_listener {message}")

    async def market_status_listener(self, message):
        data = message["body"]
        logger.debug(f"market_status, {data}")

        jangubun = data["jangubun"]
        jstatus = data["jstatus"]
        if jangubun in ["5", "8"] and jstatus in ["21", "41"]:
            if jstatus == "21":
                self._market_status = MarketStatus.Open
            elif jstatus == "41":
                self._market_status = MarketStatus.Closed

            self._market_status_updated_at = time.monotonic()

    def is_market_open(self):
        now = time.monotonic()
        if self._market_status_updated_at and now - self._market_status_updated_at < 5:
            return self._market_status == MarketStatus.Open
        return False

    def open_market_type(self):
        now = now_local()
        time = now.time()
        hour = now.hour
        time_hour = pendulum.time(hour)

        day_intervals = [[pendulum.time(8, 45), pendulum.time(15, 45)]]
        night_intervals = [
            [pendulum.time(18), pendulum.time(23)],
            [pendulum.time(0), pendulum.time(6)],
        ]
        for interval in day_intervals:
            if interval[0] <= time <= interval[1]:
                return MarketType.FutureOptionDay

        for interval in night_intervals:
            if interval[0] <= time_hour <= interval[1]:
                return MarketType.FutureOptionNight

        return MarketType.Undefined
