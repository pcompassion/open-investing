#!/usr/bin/env python3

from enum import Enum, auto

from open_investing.exchange.const.market_type import MarketType

from open_investing.exchange.ebest.api_data import EbestApiData

from open_investing.order.const.order import OrderDirection, OrderPriceType


class IndexCode(Enum):
    Kospi = "kospi"
    Kospi200 = "kospi200"
    Krx100 = "krx100"
    Kosdaq = "kosdaq"
    Vkospi = "vkospi"


class EbestApiField:
    field_name_map = {
        MarketType.STOCK: {
            "security_code": "IsuNo",
            "order_quantity": "OrdQty",
            "order_price": "OrdPrc",
            "order_direction": "BnsTpCode",
            "order_price_type": "OrdprcPtnCode",
        },
        MarketType.DERIVATIVE: {
            "security_code": "FnoIsuNo",
            "order_quantity": "OrdQty",
            "order_price": "FnoOrdPrc",
            "order_direction": "BnsTpCode",
            "order_price_type": "FnoOrdprcPtnCode",
        },
        MarketType.UNDEFINED: {},
    }

    field_value_map = {
        OrderDirection.SELL: "1",
        OrderDirection.BUY: "2",
        OrderPriceType.LIMIT: "00",
        OrderPriceType.MARKET: "03",
        IndexCode.Kospi: "001",
        IndexCode.Kospi200: "101",
        IndexCode.Krx100: "501",
        IndexCode.Kosdaq: "301",
        IndexCode.Vkospi: "205",
    }

    @classmethod
    def get_interval(cls, kind="time", interval_second=0, tr_code=None):
        res = {}

        if kind == "time":
            res["cgubun"] = "B"
        elif kind == "tick":
            res["cgubun"] = "T"

        if interval_second == 30:
            res["bgubun"] = 0
        else:
            res["bgubun"] = interval_second // 60

        return res

    @classmethod
    def get_send_data(cls, tr_code=None, *args, **kwargs):
        res = {}

        data_dict = {}
        if args:
            if len(args) > 1:
                raise ValueError(
                    "Only one positional argument (a dictionary) is allowed"
                )
            if not isinstance(args[0], dict):
                raise TypeError("The positional argument must be a dictionary")
            data_dict = args[0]

        if kwargs:
            data_dict.update(kwargs)

        for k, v in data_dict.items():
            field_name = cls.get_field_name(k, tr_code=tr_code)

            if field_name:
                value = cls.field_value_map.get(v, v)
                res[field_name] = value

        return res

    @classmethod
    def _get_field_name_map(cls, tr_code=None):
        fn_map = {}
        fn_map_tr = {}
        if tr_code:
            fn_map_tr = EbestApiData.get_field_name_map(tr_code)

        fn_map = cls.field_name_map[MarketType.UNDEFINED]

        market_type = EbestApiData.get_market_type(tr_code)

        fn_map = fn_map | cls.field_name_map[market_type]
        fn_map = fn_map | fn_map_tr

        return fn_map

    @classmethod
    def get_field_name(cls, name, tr_code=None):
        fn_map = cls._get_field_name_map(tr_code)

        return fn_map.get(name, None)