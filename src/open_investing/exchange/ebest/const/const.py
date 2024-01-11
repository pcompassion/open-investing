#!/usr/bin/env python3
from urllib.parse import urljoin

from enum import Enum


class EbestUrl:
    auth: str = "/oauth2/token"
    stock_market_data: str = "/stock/market-data"
    option_market_data: str = "/futureoption/market-data"

    stock_chart_data: str = "/stock/chart"
    option_chart_data: str = "/futureoption/chart"

    stock_invest_info: str = "/stock/investinfo"
    stock_order: str = "/stock/order"
    option_order: str = "/futureoption/order"

    market_indicator: str = "/indtp/market-data"
    market_indicator_chart: str = "/indtp/chart"

    def __init__(self):
        self.base_url: str = "https://openapi.ebestsec.co.kr:8080"

    def auth_url(self):
        return urljoin(self.base_url, self.auth)

    def get_url_for_api_path(self, api_path: str):
        return urljoin(self.base_url, api_path)

    def get_url_for_tr_code(self, tr_code: str):
        from open_investing.exchange.ebest.api_data import EbestApiData

        api_path = EbestApiData.get_api_path(tr_code)
        return self.get_url_for_api_path(api_path)


class EbestCode:
    # t2105 선물/옵션현재가호가조회, 선물/옵션챠트(N분)
    shcode: str = "shcode"
    # t2101 선물/옵션현재가(시세)조회
    focode: str = "focode"
    # t8435 파생종목마스터조회API용
    gubun: str = "gubun"
    # t3521 해외지수조회(API용)
    symbol: str = "symbol"
    # t0425 주식체결/미체결
    expcode: str = "expcode"

    # t1511 업종현재가
    upcode: str = "upcode"

    dummy: str = "dummy"
