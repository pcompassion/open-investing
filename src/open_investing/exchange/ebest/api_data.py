#!/usr/bin/env python3
from open_investing.order.const.order import OrderPriceType
import pendulum
from open_investing.const.code_name import DerivativeType, FieldName

from open_investing.exchange.const.market import MarketSecurityType
from open_investing.exchange.ebest.const.const import EbestUrl, EbestCode


class EbestApiData:
    API_DATA = {
        "t1301": {
            "body": {"cvolume": 0, "starttime": "", "endtime": "", "cts_time": ""},
            "page_key_names": ["cts_time"],
            "api_path": EbestUrl.stock_market_data,
            "market_security_type": MarketSecurityType.STOCK,
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.shcode,
            },
            "f_page_meta_block_name": "{tr_code}OutBlock",
            "f_data_block_name": "{tr_code}OutBlock1",
            "request_per_second": 2,
        },
        "t1511": {
            "body": {},
            "field_name_map": {
                FieldName.INDEX_CODE: EbestCode.upcode,
            },
            "api_path": EbestUrl.market_indicator,
            "request_per_second": 3,
        },
        "t2105": {
            "body": {},
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.shcode,
            },
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 3,
        },
        "t2101": {
            "body": {},
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.focode,
            },
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 3,
        },
        "t2830": {
            "body": {},
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.focode,
            },
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 3,
        },
        "t2301": {
            "body": {
                "gubun": "G",
            },
            "f_data_block_name": "{tr_code}OutBlock1",
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 2,
        },
        "t2835": {
            "body": {
                "gubun": "G",
            },
            "f_data_block_name": "{tr_code}OutBlock1",
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 2,
        },
        "t2209": {
            "body": {"cgubun": "B", "bgubun": 0, "cnt": 900},
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.focode,
            },
            "f_page_meta_block_name": "{tr_code}OutBlock1",
            "f_data_block_name": "{tr_code}OutBlock1",
            "api_path": EbestUrl.option_chart_data,
            "request_per_second": 1,
            "time_interval": [pendulum.time(8), pendulum.time(16)],
        },
        "t3521": {
            "api_path": EbestUrl.stock_invest_info,
            "request_per_second": 1,
        },
        "t8429": {
            "body": {"cgubun": "B", "bgubun": 0, "cnt": 900},
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.focode,
            },
            "f_page_meta_block_name": "{tr_code}OutBlock1",
            "f_data_block_name": "{tr_code}OutBlock1",
            "api_path": EbestUrl.option_chart_data,
            "request_per_second": 1,
            "time_interval": [pendulum.time(18), pendulum.time(5)],
        },
        "t8415": {
            # 선물/옵션챠트(N분)
            "body": {
                "ncnt": 0,
                "sdate": "20231108",
                "edate": "20231110",
                "nday": "1",
                "stime": "000000",
                "etime": "000000",
                "comp_yn": "N",
                "cts_date": "" * 8,
                "cts_time": "" * 10,
            },
            "page_key_names": ["cts_date", "cts_time"],
            "api_path": EbestUrl.option_chart_data,
            "market_security_type": MarketSecurityType.DERIVATIVE,
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.shcode,
            },
            "f_data_block_name": "{tr_code}OutBlock1",
            "request_per_second": 1,
        },
        "t8418": {
            "body": {
                "ncnt": 0,
                "comp_yn": "N",
                "cts_date": "" * 8,
                "cts_time": "" * 10,
            },
            "page_key_names": ["cts_time", "cts_date"],
            "f_data_block_name": "{tr_code}OutBlock1",
            "api_path": EbestUrl.market_indicator_chart,
        },
        "t8432": {
            "body": {
                "dummy": "",
            },
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 2,
        },
        "t8433": {
            "body": {
                "dummy": "",
            },
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 2,
        },
        "t8435": {
            # - 최근월 미니선물 2개: t8435에서 종목 마스터 조회후 상위2개 (TR.md 참조)
            "field_name_map": {
                FieldName.DERIVATIVE_NAME: EbestCode.gubun,
            },
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 2,
        },
        "t8437": {
            # - 최근월 미니선물 2개: t8435에서 종목 마스터 조회후 상위2개 (TR.md 참조)
            "field_name_map": {
                FieldName.DERIVATIVE_NAME: EbestCode.gubun,
            },
            "field_value_map": {
                DerivativeType.MiniFuture: "NM",
                DerivativeType.Future: "NF",
                DerivativeType.Option: "NO",
            },
            "api_path": EbestUrl.option_market_data,
            "request_per_second": 2,
        },
        "t0425": {
            "field_name_map": {
                FieldName.SECURITY_CODE: EbestCode.expcode,
            },
            "request_per_second": 1,
        },
        # order
        "CSPAT00601": {
            "api_path": EbestUrl.stock_order,
            "f_data_block_name": "{tr_code}OutBlock1",
            "body": {
                "MgntrnCode": "000",
                "OrdCndiTpCode": "0",
                "LoanDt": "",
            },
            "market_security_type": MarketSecurityType.STOCK,
            "f_in_block_name": "{tr_code}InBlock1",
            "request_per_second": 10,
        },
        "CFOAT00100": {
            "api_path": EbestUrl.option_order,
            "f_data_block_name": "{tr_code}OutBlock1",
            "f_in_block_name": "{tr_code}InBlock1",
            "market_security_type": MarketSecurityType.DERIVATIVE,
            "request_per_second": 10,
            "non_recoverble_codes": ["01491"],
        },
        "CEXAT11100": {
            "api_path": EbestUrl.option_order,
            "f_data_block_name": "{tr_code}OutBlock1",
            "f_in_block_name": "{tr_code}InBlock1",
            "market_security_type": MarketSecurityType.DERIVATIVE,
            "request_per_second": 5,
            "field_name_map": {
                "order_price_type": "ErxPrcCndiTpCode",
            },
            "field_value_map": {
                OrderPriceType.Market: "1",
                OrderPriceType.Limit: "2",
            },
            "non_recoverble_codes": ["01491"],
        },
        "CFOAT00300": {
            "api_path": EbestUrl.option_order,
            "market_security_type": MarketSecurityType.DERIVATIVE,
            "f_in_block_name": "{tr_code}InBlock1",
            "f_data_block_name": "{tr_code}OutBlock1",
            "request_per_second": 10,
        },
        "CEXAT11300": {
            "api_path": EbestUrl.option_order,
            "market_security_type": MarketSecurityType.DERIVATIVE,
            "f_in_block_name": "{tr_code}InBlock1",
            "f_data_block_name": "{tr_code}OutBlock1",
            "request_per_second": 10,
        },
    }

    @classmethod
    def get_field_name_map(cls, tr_code):
        fn_map = {}
        if tr_code in cls.API_DATA:
            fn_map = cls.API_DATA[tr_code].get("field_name_map", {})

        return fn_map

    @classmethod
    def get_field_value_map(cls, tr_code):
        fn_map = {}
        if tr_code in cls.API_DATA:
            fn_map = cls.API_DATA[tr_code].get("field_value_map", {})

        return fn_map

    @classmethod
    def get_field_name(cls, tr_code, name):
        from open_investing.exchange.ebest.api_field import EbestApiField

        return EbestApiField.get_field_name(name, tr_code)

    @classmethod
    def get_market_security_type(cls, tr_code):
        market_security_type = MarketSecurityType.UNDEFINED

        if tr_code in cls.API_DATA:
            market_security_type = cls.API_DATA[tr_code].get(
                "market_security_type", MarketSecurityType.UNDEFINED
            )

        return market_security_type

    @classmethod
    def get_api_path(cls, tr_code):
        api_path = cls.API_DATA.get(tr_code, {}).get("api_path")
        return api_path

    @classmethod
    def get_api_data(cls, tr_code):
        return cls.API_DATA.get(tr_code, {})

    @classmethod
    def get_in_block_name(cls, tr_code):
        api_data = EbestApiData.get_api_data(tr_code)

        in_block_name: str = api_data.get("f_in_block_name", "{tr_code}InBlock").format(
            tr_code=tr_code
        )

        return in_block_name

    @classmethod
    def get_data_block_name(cls, tr_code):
        api_data = EbestApiData.get_api_data(tr_code)

        data_block_name: str = api_data.get(
            "f_data_block_name", "{tr_code}OutBlock"
        ).format(tr_code=tr_code)

        return data_block_name

    @classmethod
    def get_page_meta_block_name(cls, tr_code):
        api_data = EbestApiData.get_api_data(tr_code)
        block_name: str = api_data.get(
            "f_page_meta_block_name", "{tr_code}OutBlock"
        ).format(tr_code=tr_code)

        return block_name

    @classmethod
    def get(cls, tr_code, name, default=None):
        api_data = cls.get_api_data(tr_code)
        return api_data.get(name, default)

    @classmethod
    def is_recoverable(cls, tr_code, error_code):
        api_data = cls.get_api_data(tr_code)

        non_recoverable_codes = api_data.get("non_recoverable_codes") or []
        if error_code in non_recoverable_codes:
            return False
        recoverable_codes = api_data.get("recoverable_codes") or []
        if error_code in recoverable_codes:
            return True

        return None
