#!/usr/bin/env python3

from decimal import Decimal
from open_investing.exchange.const.market import MarketType
import asyncio
from datetime import time
import pendulum

from open_investing.security.derivative_code import DerivativeCode

from open_investing.event_spec.event_spec import OrderEventSpec
from open_investing.order.const.order import OrderEventName, OrderPriceType, OrderSide
from open_investing.exchange.ebest.api_field import EbestApiField
from open_library.time.datetime import combine, now_local
from open_library.collections.dict import rename_keys, to_jsonable_python
import logging
from open_investing.price.money import Money
from open_library.asynch.queue import call_function_after_delay

logger = logging.getLogger(__name__)


class OrderMixin:
    async def open_order(self, order):
        security_code = order.security_code
        market_type = self.open_market_type()

        tr_code = None
        api = None
        try:
            derivative_code = DerivativeCode.from_string(security_code)
            tr_code = "CFOAT00100"
            api = self.derivative_api

            if market_type == MarketType.FutureOptionDay:
                tr_code = "CFOAT00100"
            elif market_type == MarketType.FutureOptionNight:
                tr_code = "CEXAT11100"

        except ValueError:
            tr_code = "CSPAT00601"
            api = self.stock_api

        order_price_type = order.order_price_type

        security_code = order.security_code
        quantity = order.quantity_order
        side = order.side

        additional = {}

        match order_price_type:
            case OrderPriceType.Market:
                pass
            case OrderPriceType.Limit:
                additional.update(dict(order_price=float(str(order.price.amount))))

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
            exchange_order_id = api_response.raw_data[f"{tr_code}OutBlock2"].get(
                "OrdNo"
            )

            if exchange_order_id:
                exchange_order_id = str(int(exchange_order_id))

        if not exchange_order_id:
            logger.warning(f"open_order fail, {order.id}")

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

    async def derivative_order_listener(self, message, retry=True):
        logger.info(f"derivative_order_listener {message}, retry: {retry}")
        tr_code = message["header"]["tr_cd"]
        data = message.get("body")

        if tr_code == "C01":
            security_code = data["expcode"]
            quantity = int(data["chevol"])

            date_str = data["chedate"]
            time_str = data["chetime"]
            date_format = "YYYYMMDD"
            # time_format = "HHmmssSSS"

            dt = pendulum.from_format(date_str, date_format)
            date = dt.date()

            price_amount = data["cheprice"]

        elif tr_code == "EU1":
            security_code = data["fnoIsuno"]
            quantity = int(data["execqty"])

            time_str = data["ctrcttime"]
            now = now_local()
            date = now.date()
            if now.time().hour < int(time_str[:2]):
                date = date.subtract(days=1)

            price_amount = data["execprc"]

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
            microsecond=milliseconds * 1000,  # Convert milliseconds to microseconds
        )
        # Output: 2024-01-18
        date_at = combine(date, time_obj)

        exchange_order_id = data["ordno"]
        match tr_code:
            case None:
                pass
            case _:
                exchange_order_id = str(int(exchange_order_id))

                order = await self.order_data_manager.get_single_order(
                    filter_params=dict(exchange_order_id=exchange_order_id)
                )

                if order is None:
                    logger.warning(
                        f"order not found for exchange_order_id: {exchange_order_id}, retry: {retry}"
                    )
                    if retry:
                        orders = await self.order_data_manager.pending_orders(
                            exchange_order_id=exchange_order_id
                        )
                        if orders:
                            delay_seconds = 1
                            task = asyncio.create_task(
                                call_function_after_delay(
                                    self.derivative_order_listener,
                                    delay_seconds,
                                    message,
                                    retry=False,
                                )
                            )
                            self.running_tasks.add(task)
                            task.add_done_callback(
                                lambda t: self.running_tasks.remove(t)
                            )
                    else:
                        logger.warning(
                            f"order not found after retry.. for exchange_order_id: {exchange_order_id}"
                        )

                    return

                order_event_spec = OrderEventSpec(
                    name=OrderEventName.ExchangeFilled,
                    order_id=order.id,
                )

                data = dict(
                    security_code=security_code,
                    fill_quantity_order=quantity,
                    fill_price=Money(amount=price_amount, currency="KRW"),
                    date_at=date_at,
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
        cancel_quantity_order: Decimal,
        order,
    ):
        tr_code = "CFOAT00300"
        market_type = self.open_market_type()

        if market_type == MarketType.FutureOptionDay:
            tr_code = "CFOAT00300"

        elif market_type == MarketType.FutureOptionNight:
            tr_code = "CEXAT11300"

        send_data = EbestApiField.get_send_data(
            tr_code=tr_code,
            security_code=security_code,
            cancel_quantity=int(cancel_quantity_order),
            exchange_order_id=int(order.exchange_order_id),
        )

        api = self.derivative_api

        api_response = await api.open_order(tr_code, send_data=send_data)

        result = rename_keys(
            api_response.data,
            key_mapping=dict(
                CancQty="cancelled_quantity_order",
                OrgOrdNo="open_order_id",
                OrdNo="cancel_order_id",
            ),
        )

        if "cancel_order_id" in result:
            result["cancel_order_id"] = Decimal(result["cancel_order_id"])

        return result, api_response
