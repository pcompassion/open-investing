#!/usr/bin/env python3

from datetime import time
import pendulum

from open_investing.security.derivative_code import DerivativeCode

from open_investing.event_spec.event_spec import OrderEventSpec
from open_investing.order.const.order import OrderEventName, OrderPriceType, OrderSide
from open_investing.exchange.ebest.api_field import EbestApiField
from open_library.time.datetime import combine
from open_library.collections.dict import rename_keys
import logging
from open_investing.price.money import Money

logger = logging.getLogger(__name__)


class OrderMixin:
    async def open_order(self, order):
        security_code = order.security_code

        tr_code = None
        api = None
        try:
            derivative_code = DerivativeCode.from_string(security_code)
            tr_code = "CFOAT00100"
            api = self.derivative_api

        except ValueError:
            tr_code = "CSPAT00601"
            api = self.stock_api

        order_price_type = order.order_price_type

        security_code = order.security_code
        quantity = order.quantity
        side = order.side

        additional = {}

        match order_price_type:
            case OrderPriceType.Market:
                pass
            case OrderPriceType.Limit:
                additional.update(dict(order_price=order.price_amount))

        send_data = EbestApiField.get_send_data(
            tr_code=tr_code,
            security_code=security_code,
            order_quantity=int(quantity),
            order_side=side,
            order_price_type=order_price_type,
            **additional,
        )

        api_response = await api.open_order(
            tr_code, send_data=send_data, default_data_type=dict
        )
        exchange_order_id = None
        if api_response.success:
            if tr_code == "CFOAT00100":
                exchange_order_id = api_response.raw_data["CFOAT00100OutBlock2"].get(
                    "OrdNo"
                )
            elif tr_code == "CSPAT00601":
                exchange_order_id = api_response.raw_data["CSPAT00601OutBlock2"].get(
                    "OrdNo"
                )
            if exchange_order_id:
                exchange_order_id = int(exchange_order_id)

        return exchange_order_id, api_response

    async def stock_order_listener(self, message):
        logger.info(f"stock_order_listener {message}")

        tr_cd = message["header"]["tr_cd"]
        data = message.get("body")
        match tr_cd:
            case None:
                pass
            case _:
                security_code = data["shtnIsuNo"]
                logger.info(f"order ack security_code: {security_code}")

    async def derivative_order_listener(self, message):
        logger.info(f"derivative_order_listener {message}")
        tr_cd = message["header"]["tr_cd"]
        data = message.get("body")
        match tr_cd:
            case None:
                pass
            case _:
                security_code = data["expcode"]
                exchange_order_id = data["ordno"]
                exchange_order_id = int(exchange_order_id)

                order = await self.order_data_manager.get_single_order(
                    filter_params=dict(exchange_order_id=exchange_order_id)
                )

                if order is None:
                    logger.warning(
                        f"order not found for exchange_order_id: {exchange_order_id}"
                    )
                    return

                order_event_spec = OrderEventSpec(
                    name=OrderEventName.ExchangeFilled,
                    order_id=order.id,
                )

                date_str = data["chedate"]
                time_str = data["chetime"]
                date_format = "YYYYMMDD"
                time_format = "HHmmssSSS"

                dt = pendulum.from_format(date_str, date_format)
                date = dt.date()

                # time = pendulum.parse(time_str, exact=True, formatter=time_format)

                hours, minutes, seconds = (
                    int(time_str[:2]),
                    int(time_str[2:4]),
                    int(time_str[4:6]),
                )
                milliseconds = int(time_str[6:])

                # Create a time object
                time_obj = time(
                    hour=hours,
                    minute=minutes,
                    second=seconds,
                    microsecond=milliseconds
                    * 1000,  # Convert milliseconds to microseconds
                )
                # Output: 2024-01-18

                data = dict(
                    security_code=security_code,
                    fill_quantity=int(data["chevol"]),
                    fill_price=Money(amount=data["cheprice"], currency="KRW"),
                    date_at=combine(date, time_obj),
                )

                message = dict(
                    event_spec=order_event_spec,
                    order=order,
                    data=data,
                )

                await self.order_event_broker.enqueue_message(message)

    async def cancel_order_quantity(
        self,
        security_code: str,
        cancel_quantity: float,
        order,
    ):
        tr_code = "CFOAT00300"

        send_data = EbestApiField.get_send_data(
            tr_code=tr_code,
            security_code=security_code,
            cancel_quantity=cancel_quantity,
            exchange_order_id=order.exchange_order_id,
        )

        api = self.derivative_api

        api_response = await api.open_order(tr_code, send_data=send_data)

        result = rename_keys(
            api_response.data,
            key_mapping=dict(
                CancQty="cancelled_quantity",
                OrgOrdNo="open_order_id",
                OrdNo="cancel_order_id",
            ),
        )

        return result, api_response
