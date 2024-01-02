#!/usr/bin/env python3


from open_investing.order.const.order import OrderPriceType, OrderSide
from open_investing.exchange.ebest.api_field import EbestApiField


class OrderMixin:
    async def market_order(
        self, security_code: str, quantity: float, side: OrderSide, data_manager=None
    ):
        order_price_type = OrderPriceType.Market

        # tr_code = "CSPAT00601"
        tr_code = "CFOAT00100"

        send_data = EbestApiField.get_send_data(
            tr_code=tr_code,
            security_code=security_code,
            order_quantity=quantity,
            order_price_type=order_price_type,
        )

        order = data_manager.unsaved_order(
            params=dict(
                security_code=security_code,
                quantity=quantity,
                side=side,
                order_price_type=order_price_type,
            )
        )

        api = self.derivative_api

        api_response = await api.order_action(tr_code, send_data=send_data)

        exchange_order_id = api_response.data["ordno"]

        order = await data_manager.save(
            order, save_params=dict(exchange_order_id=exchange_order_id)
        )

        return order, api_response

    async def stock_order_listener(self, data):
        print("stock_order_listener", data)

        security_code = data["shtnIsuNo"]

    async def derivative_order_listener(self, data):
        print("stock_order_listener", data)

        security_code = data["expcode"]
        exchange_order_id = data["ordno"]

        order = await order_data_manager.get_order(exchange_order_id=exchange_order_id)

        message = data

        order_update_broker.enqueue_message(order.id, message)
