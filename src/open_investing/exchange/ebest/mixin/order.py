#!/usr/bin/env python3


from open_investing.order.const.order import OrderPriceType, OrderSide
from open_investing.exchange.ebest.api_field import EbestApiField
from open_library.time.datetime import combine


class OrderMixin:
    async def market_order(
        self,
        security_code: str,
        quantity: float,
        side: OrderSide,
        order: Order,
    ):
        order_price_type = OrderPriceType.Market

        # tr_code = "CSPAT00601"
        tr_code = "CFOAT00100"

        send_data = EbestApiField.get_send_data(
            tr_code=tr_code,
            security_code=security_code,
            order_quantity=quantity,
            order_side=side,
            order_price_type=order_price_type,
        )

        api = self.derivative_api

        api_response = await api.order_action(tr_code, send_data=send_data)

        exchange_order_id = api_response.data["ordno"]

        return exchange_order_id, api_response

    async def stock_order_listener(self, data):
        print("stock_order_listener", data)

        security_code = data["shtnIsuNo"]

    async def derivative_order_listener(self, data):
        print("stock_order_listener", data)

        security_code = data["expcode"]
        exchange_order_id = data["ordno"]

        order = await order_data_manager.get(exchange_order_id=exchange_order_id)

        order_exchange_event = OrderExchangeEvent(
            name=OrderExchangeEventName.Filled,
            data=dict(
                fill_quantity=data["chevol"],
                fill_price=data["cheprice"],
                date_at=combine(data["chedate"], data["chetime"]),
            ),
        )

        order_exchange_event_broker.enqueue_message(
            order.id, dict(order_exchange_event=order_exchange_event, order=order)
        )
