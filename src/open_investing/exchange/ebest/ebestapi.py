#!/usr/bin/env python3
import sys

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


from open_investing.exchange.ebest.api_data import EbestApiData

from open_library.logging.logging_filter import WebsocketLoggingFilter
from open_investing.exchange.ebest.const.const import EbestUrl
from open_investing.const.code_name import FieldName


from open_library.api_client.websocket_client import WebSocketClient
from open_library.api_client.api_client import ApiClient, ApiResponse
from open_library.environment.const import Env
from open_investing.exchange.exchange_api import ExchangeApi


logger = logging.getLogger(__name__)


HEADERS_DATA = {
    "headers": {
        "tr_cont": "N",
        "tr_cont_key": "",
    }
}


class EbestApi(ExchangeApi):
    name: str = "ebest"
    _instances: Dict[str, "EbestApi"] = {}

    last_api_request_times: dict[str, float] = {}

    @classmethod
    async def get_instance(cls, app_key, app_secret):
        if app_key not in cls._instances:
            instance = cls(app_key, app_secret)
            cls._instances[app_key] = instance
        return cls._instances[app_key]

    def __init__(self, api_key: str, api_secret: str, env: Env = Env.DEV):
        self.api_key: str = api_key
        self.api_secret: str = api_secret

        self.url = EbestUrl()
        self.api_client = ApiClient(
            self.url.auth_url(),
            api_key,
            api_secret,
            should_refresh_token_func=self.should_refresh_token_func,
        )

        self.env = env

        self.ws_clients: Dict[str, WebSocketClient] = {}  # not used
        self.ws_client: WebSocketClient = None

        self.shutdown_event = asyncio.Event()

    def start_token_refresh(self):
        token_manager = self.api_client.get_token_manager()
        token_manager.start_refresh_task()

    def should_refresh_token_func(self, response: httpx.Response):
        data = response.json()
        rsp_cd = data["rsp_cd"]

        token_refresh_response_codes = ["IGW00121"]

        if response.status_code == 401 or (
            response.status_code == 500 and rsp_cd in token_refresh_response_codes
        ):
            return True
        return False

    def get_or_create_ws_client(self, tr_type) -> WebSocketClient:
        token_manager = self.api_client.get_token_manager()
        ws_uri: str = ""
        match self.env:
            case Env.DEV:
                ws_uri = "wss://openapi.ebestsec.co.kr:29443/websocket"
            case Env.PROD:
                ws_uri = "wss://openapi.ebestsec.co.kr:9443/websocket"

        # headers = {"tr_type": tr_type}
        if not self.ws_client:
            self.ws_client = WebSocketClient(
                ws_uri, token_manager, self.topic_extractor
            )
        return self.ws_client

    def topic_extractor(self, response):
        header = response.get("header", {})
        tr_cd = header.get("tr_cd", None)
        tr_key = header.get("tr_key", "")
        body = {}
        if tr_cd:
            body = self._topic_body(tr_cd, tr_key)

        topic_key = self._dict_to_key(body)

        return topic_key

    async def _get_page_data(
        self,
        tr_code: str,
        headers: Dict[str, Any],
        page_key_data: Dict[str, Any],
        body_block: Dict[str, Any],
    ):
        data_block_name: str = EbestApiData.get_data_block_name(tr_code)
        page_meta_block_name: str = EbestApiData.get_page_meta_block_name(tr_code)

        headers["tr_cont"] = "Y"

        out_block_data = []

        while page_key_data and all(value for value in page_key_data.values()):
            body_block_updated = {**body_block, **page_key_data}

            api_response = await self.get_market_data(
                tr_code,
                headers=headers,
                send_data=body_block_updated,
                all_page=False,
            )
            data = api_response.raw_data

            page_meta_block_data = data[page_meta_block_name]

            for page_key_name in page_key_data.keys():
                page_key_data[page_key_name] = page_meta_block_data.get(
                    page_key_name, None
                )

            out_block_data.extend(data[data_block_name])

        return out_block_data

    def _get_body_header(
        self,
        tr_code: str,
        headers: Optional[Dict[str, Any]] = None,
        send_data: Optional[Dict[str, Any]] = None,
    ):
        from open_investing.exchange.ebest.api_field import EbestApiField

        send_data = send_data or {}
        api_data = EbestApiData.get_api_data(tr_code)

        default_body = api_data.get("body", {}).copy() or {}
        send_data_updated = EbestApiField.get_send_data(tr_code=tr_code, **send_data)

        send_data_updated = {**default_body, **send_data_updated}

        headers = headers or {}
        default_headers = HEADERS_DATA.get("headers", {}).copy() or {}
        headers = {**default_headers, **headers}

        headers["tr_cd"] = tr_code

        in_block_name: str = EbestApiData.get_in_block_name(tr_code)

        body = {in_block_name: send_data_updated}

        return {
            "body": body,
            "in_block_name": in_block_name,
            "headers": headers,
        }

    async def get_market_data(
        self,
        tr_code: str,
        send_data: Optional[dict[Any, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
        all_page: Optional[bool] = True,
        handler: Optional[Callable[[ApiResponse], Awaitable[None]]] = None,
        default_data_type=list,
    ):
        body_header = self._get_body_header(tr_code, headers, send_data)

        body = body_header["body"]
        headers_updated = body_header["headers"]
        in_block_name = body_header["in_block_name"]
        body_block = body[in_block_name]

        api_data = EbestApiData.get_api_data(tr_code)

        url = self.url.get_url_for_tr_code(tr_code)

        last_api_request_time = self.last_api_request_times.get(tr_code, None)
        if last_api_request_time is not None:
            elapsed = time.monotonic() - last_api_request_time
            required_sec = 1.0 / api_data.get("request_per_second", 1.0)

            # if self.env == Env.DEV:
            #     required_sec *= 5

            if elapsed < required_sec:
                await asyncio.sleep(required_sec - elapsed)

        self.last_api_request_times[tr_code] = time.monotonic()

        response = await self.api_client.request(
            url, "POST", headers=headers_updated, json=body
        )

        data_block_name: str = EbestApiData.get_data_block_name(tr_code)

        data = response.json() or {}

        logger.info(f"request data: {body}, response msg: {data.get('rsp_msg','')}")

        rsp_cd = data.get("rsp_cd", -1)
        try:
            rsp_cd = int(rsp_cd)
            if rsp_cd != 0:
                raise
        except:
            logger.warning(f"request: {body}, data: {data}")
            return ApiResponse(
                success=False,
                raw_data=data,
                headers=response.headers,
                data_field_name=data_block_name,
                error_code=rsp_cd,
                exchange_api_code=tr_code,
                default_data_type=default_data_type,
            )

        out_block_data = data.get(data_block_name, None)
        api_response = ApiResponse(
            success=True,
            raw_data=data,
            headers=response.headers,
            data_field_name=data_block_name,
            exchange_api_code=tr_code,
            default_data_type=default_data_type,
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
                headers=headers_updated,
                page_key_data=page_key_data,
                body_block=body_block,
            )

            out_block_data.extend(page_data)

        if handler:
            await handler(api_response)

        return api_response

    async def open_order(
        self,
        tr_code: str,
        headers: Optional[Dict[str, Any]] = None,
        send_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        return await self.get_market_data(
            tr_code, headers=headers, send_data=send_data, **kwargs
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

        header = {"tr_type": tr_type}
        topic_key = self._dict_to_key(body)

        await ws_client.subscribe(topic_key, handler, header, body)

    async def unsubscribe(
        self,
        tr_type: str,
        tr_code: str,
        tr_key: str,
        handler: Callable[[str], Awaitable[None]],
    ):
        ws_client = self.get_or_create_ws_client(tr_type)
        body = self._topic_body(tr_code, tr_key)
        header = {"tr_type": tr_type}
        topic_key = self._dict_to_key(body)

        await ws_client.unsubscribe(topic_key, handler, header, body)

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
