#!/usr/bin/env python3


from open_investing.security.derivative_code import DerivativeCode
from open_investing.order.order_event_broker import OrderEvent
from open_investing.order.const.order import OrderEventName, OrderPriceType, OrderSide
from open_investing.exchange.ebest.api_field import EbestApiField
from open_library.time.datetime import combine
from open_library.collections.dict import rename_keys
import logging

logger = logging.getLogger(__name__)


class OrderMixin:
    async def open_order(self, order):
        security_code = order.security_code

        tr_code = None
        api = None
        try:
            derivative_code = DerivativeCode.from_string(security_code)
            tr_code = "CFOAT00100"
            api = self.stock_api
        except ValueError:
            tr_code = "CSPAT00601"
            api = self.derivative_api

        order_price_type = order.order_price_type

        security_code = order.security_code
        quantity = order.quantity
        side = order.side

        send_data = EbestApiField.get_send_data(
            tr_code=tr_code,
            security_code=security_code,
            order_quantity=int(quantity),
            order_side=side,
            order_price_type=order_price_type,
        )

        match order_price_type:
            case OrderPriceType.Market:
                pass
            case OrderPriceType.Limit:
                send_data.update(dict(price=order.price))

        api_response = await api.open_order(
            tr_code, send_data=send_data, default_data_type=dict
        )

        exchange_order_id = api_response.data.get("ordno")

        return exchange_order_id, api_response

    async def stock_order_listener(self, message):
        logger.info(f"stock_order_listener {message}")
        return
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

                order = await order_data_manager.get(
                    exchange_order_id=exchange_order_id
                )

                order_event = OrderEvent(
                    name=OrderEventName.ExchangeFilled,
                    data=dict(
                        fill_quantity=data["chevol"],
                        fill_price=data["cheprice"],
                        date_at=combine(data["chedate"], data["chetime"]),
                    ),
                )

                order_event_broker.enqueue_message(
                    order.id, dict(order_event=order_event, order=order)
                )

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
                OrgOrdNo="exchange_order_id",
                OrdNo="cancel_order_id",
            ),
        )

        return result, api_response
