#!/usr/bin/env python3
import sys

# if "/Users/littlehome/projects/risk-glass/src/" not in sys.path:
#     sys.path.append("d:/dev/XingAPI/risk/src/")

import requests
import json
from pathlib import Path
import time
from datetime import datetime, timedelta
from enum import Enum, auto

from typing import Any, Dict, Optional, Callable, Awaitable
import httpx
import asyncio
import websockets
import logging
import pendulum


from risk_glass.ebest.openapi.settings import ENVIRONMENT, Environment
from open_investing.exchange.ebest.api_data import EbestApiData

from open_library.logging.logging_filter import WebsocketLoggingFilter
from open_investing.exchange.ebest.const.const import FieldName, EbestUrl


from open_library.api_client.websocket_client import WebSocketClient
from open_library.api_client.api_client import ApiClient, ApiResponse


logger = logging.getLogger(__name__)


HEADERS_DATA = {
    "headers": {
        "tr_cont": "N",
        "tr_cont_key": "",
    }
}


class EbestApi:
    name: str = "ebest"
    _instances: Dict[str, "EbestApi"] = {}

    @classmethod
    async def get_instance(cls, app_key, app_secret):
        if app_key not in cls._instances:
            instance = cls(app_key, app_secret)
            cls._instances[app_key] = instance
        return cls._instances[app_key]

    def __init__(self, api_key: str, api_secret: str):
        self.api_key: str = api_key
        self.api_secret: str = api_secret

        self.url = EbestUrl()
        self.api_client = ApiClient(self.url.auth_url(), api_key, api_secret)

        self.ws_clients: Dict[str, WebSocketClient] = {}
        self.shutdown_event = asyncio.Event()

    def get_or_create_ws_client(self, tr_type) -> WebSocketClient:
        token_manager = self.api_client.get_token_manager()
        ws_uri: str = ""
        match ENVIRONMENT:
            case Environment.DEV:
                ws_uri = "wss://openapi.ebestsec.co.kr:29443/websocket"
            case Environment.PROD:
                ws_uri = "wss://openapi.ebestsec.co.kr:9443/websocket"

        if tr_type not in self.ws_clients:
            headers = {"tr_type": tr_type}
            self.ws_clients[tr_type] = WebSocketClient(ws_uri, headers, token_manager)

        return self.ws_clients[tr_type]

    async def _get_page_data(
        self,
        tr_code: str,
        sh_code: Optional[str],
        headers: Dict[str, Any],
        page_key_data: Dict[str, Any],
    ):
        data_block_name: str = EbestApiData.get_data_block_name(tr_code)
        page_meta_block_name: str = EbestApiData.get_page_meta_block_name(tr_code)

        headers["tr_cont"] = "Y"

        out_block_data = []

        while page_key_data and all(value for value in page_key_data.values()):
            body_block = page_key_data
            api_response = await self.get_market_data(
                tr_code,
                sh_code,
                headers=headers,
                body_block=body_block,
                all_page=False,
            )
            data_page = api_response.raw_data

            page_meta_block_data = data_page[page_meta_block_name]

            for page_key_name in page_key_data.keys():
                page_key_data[page_key_name] = page_meta_block_data.get(
                    page_key_name, None
                )

            out_block_data.extend(data_page[data_block_name])

        return out_block_data

    def _get_body_header(
        self,
        tr_code: str,
        headers: Optional[Dict[str, Any]] = None,
        body_block: Optional[Dict[str, Any]] = None,
    ):
        from open_investing.exchange.ebest.api_field import EbestApiField

        body_block = body_block or {}
        api_data = EbestApiData.get_api_data(tr_code)

        default_body_block = api_data.get("body", {}).copy() or {}
        send_data = EbestApiField.get_send_data(tr_code=tr_code, **body_block)

        body_block = {**default_body_block, **send_data}

        headers = headers or {}
        default_headers = HEADERS_DATA.get("headers", {}).copy() or {}
        headers = {**default_headers, **headers}

        headers["tr_cd"] = tr_code

        in_block_name: str = EbestApiData.get_in_block_name(tr_code)

        body = {in_block_name: body_block}
        body_block = body[in_block_name]

        return {
            "body": body,
            "in_block_name": in_block_name,
            "headers": headers,
        }

    async def get_market_data(
        self,
        tr_code: str,
        sh_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        body_block: Optional[Dict[str, Any]] = None,
        all_page: Optional[bool] = True,
        handler: Optional[Callable[[str], Awaitable[None]]] = None,
    ):
        body_header = self._get_body_header(tr_code, headers, body_block)

        body = body_header["body"]
        headers_f = body_header["headers"]
        in_block_name = body_header["in_block_name"]
        body_block_f = body[in_block_name]

        api_data = EbestApiData.get_api_data(tr_code)

        code_field_name = EbestApiData.get_field_name(tr_code, FieldName.SECURITY_CODE)

        if sh_code:
            body_block_f[code_field_name] = sh_code

        url = self.url.get_url_for_tr_code(tr_code)

        response = await self.api_client.request(
            url, "POST", headers=headers_f, json=body
        )

        data_block_name: str = EbestApiData.get_data_block_name(tr_code)

        data = response.json()

        rsp_cd = data.get("rsp_cd")
        try:
            rsp_cd = int(rsp_cd)
            if rsp_cd != 0:
                raise
        except:
            logger.warning(f"data: {data}")
            return ApiResponse(
                success=False,
                raw_data=data,
                data_field_name=data_block_name,
                error_code=rsp_cd,
            )

        out_block_data = data.get(data_block_name, None)
        api_response = ApiResponse(
            success=True, raw_data=data, data_field_name=data_block_name
        )

        if all_page:
            page_meta_block_name: str = EbestApiData.get_page_meta_block_name(tr_code)

            page_meta_block_data = data.get(page_meta_block_name, {})

            page_key_names = api_data.get("page_key_names")
            if not page_key_names:
                return api_response

            page_key_data = {}
            for page_key_name in page_key_names:
                page_key_data[page_key_name] = page_meta_block_data.get(
                    page_key_name, None
                )

            page_data = await self._get_page_data(
                tr_code,
                sh_code,
                headers=headers_f,
                page_key_data=page_key_data,
            )

            out_block_data.extend(page_data)

        if handler:
            await handler(api_response)

        return api_response

    async def order_action(
        self,
        tr_code: str,
        headers: Optional[Dict[str, Any]] = None,
        body_block: Optional[Dict[str, Any]] = None,
    ):
        return await self.get_market_data(
            tr_code, headers=headers, body_block=body_block
        )

    @staticmethod
    def _dict_to_key(d) -> tuple:
        return tuple(sorted(d.items()))

    @staticmethod
    def _topic_body(tr_code: str, tr_key: str):
        body = {"tr_cd": tr_code, "tr_key": tr_key}
        return body

    async def subscribe(
        self,
        tr_type: str,
        tr_code: str,
        tr_key: str,
        handler: Callable[[str], Awaitable[None]],
    ):
        ws_client = self.get_or_create_ws_client(tr_type)
        body = self._topic_body(tr_code, tr_key)
        topic_key = self._dict_to_key(body)

        await ws_client.subscribe(body, topic_key, handler=handler)

    async def unsubscribe(self, tr_type: str, tr_code: str, tr_key: str):
        ws_client = self.get_or_create_ws_client(tr_type)
        body = self._topic_body(tr_code, tr_key)
        topic_key = self._dict_to_key(body)

        await ws_client.unsubscribe(topic_key)

    async def shutdown(self):
        logger.info("shutdown")

        token_manager = self.api_client.get_token_manager()
        token_manager.stop_refreshing()
        ws_client_keys = list(self.ws_clients.keys())

        for ws_client_key in ws_client_keys:
            ws_client = self.ws_clients[ws_client_key]
            await ws_client.close()

    async def wait_for_shutdown(self):
        await self.shutdown_event.wait()

    def trigger_shutdown(self):
        logger.info("trigger_shutdown")
        self.shutdown_event.set()

    def is_shutdown_triggered(self):
        return self.shutdown_event.is_set()
