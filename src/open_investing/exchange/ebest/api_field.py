#!/usr/bin/env python3
import re
from enum import Enum, auto

from open_investing.exchange.const.market_type import MarketType

from open_investing.exchange.ebest.api_data import EbestApiData

from open_investing.order.const.order import OrderSide, OrderPriceType
from open_investing.const.code_name import IndexCode, DerivativeType


class EbestApiField:
    field_name_map = {
        MarketType.STOCK: {
            "security_code": "IsuNo",
            "order_quantity": "OrdQty",
            "order_price": "OrdPrc",
            "order_side": "BnsTpCode",
            "order_price_type": "OrdprcPtnCode",
        },
        MarketType.DERIVATIVE: {
            "security_code": "FnoIsuNo",
            "order_quantity": "OrdQty",
            "order_price": "FnoOrdPrc",
            "order_side": "BnsTpCode",
            "order_price_type": "FnoOrdprcPtnCode",
        },
        MarketType.UNDEFINED: {
            "cancel_quantity": "CancQty",
            "exchange_order_id": "OrgOrdNo",
        },
    }

    regex_rules = [
        (re.compile(r"^bidho(\d+)$"), r"bid_price_\1"),
        (re.compile(r"^bidrem(\d+)$"), r"bid_volume_\1"),
        (re.compile(r"^offerho(\d+)$"), r"ask_price_\1"),
        (re.compile(r"^offerrem(\d+)$"), r"offer_volume_\1")
        # Add more regex rules as needed
    ]

    field_value_map = {
        OrderSide.Sell: "1",
        OrderSide.Buy: "2",
        OrderPriceType.Limit: "00",
        OrderPriceType.Market: "03",
        IndexCode.Kospi: "001",
        IndexCode.Kospi200: "101",
        IndexCode.Krx100: "501",
        IndexCode.Kosdaq: "301",
        IndexCode.Vkospi: "205",
        DerivativeType.MiniFuture: "MF",
        DerivativeType.MiniOption: "MO",
        DerivativeType.WeeklyOption: "WO",
        DerivativeType.Kosdaq150Future: "SF",
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
        """
        convert human readable data to api consumable field name and field value
        """
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
                kwargs.pop(k)

                value = cls.field_value_map.get(v, v)
                res[field_name] = value

        return kwargs | res

    @classmethod
    def get_response_data(cls, tr_code=None, **kwargs):
        res = {}

        data_dict = {}
        if kwargs:
            data_dict.update(kwargs)

        for k, v in data_dict.items():
            field_name = cls.get_field_name(k, tr_code=tr_code)

            if field_name:
                kwargs.pop(k)

                value = cls.field_value_map.get(v, v)
                res[field_name] = value

            else:
                new_key = k
                for pattern, replacement in cls.regex_rules:
                    match = pattern.match(k)
                    if match:
                        new_key = pattern.sub(replacement, k)
                        break
                res[new_key] = v

        return kwargs | res

    @classmethod
    def _get_field_name_map(cls, tr_code=None):
        fn_map = {}
        fn_map_tr = {}
        if tr_code:
            fn_map_tr = EbestApiData.get_field_name_map(tr_code)

        fn_map = cls.field_name_map[MarketType.UNDEFINED]

        market_type = EbestApiData.get_market_type(tr_code)

        # tr's map -> tr's market_type map -> general map
        fn_map = fn_map | cls.field_name_map[market_type]
        fn_map = fn_map | fn_map_tr

        return fn_map

    @classmethod
    def get_field_name(cls, name, tr_code=None):
        fn_map = cls._get_field_name_map(tr_code)

        return fn_map.get(name, None)
