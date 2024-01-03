#!/usr/bin/env python3


class OrderService:
    def __init__(self, order_data_manager, api_manager):
        self.order_data_manager = order_data_manager
        self.api_manager = api_manager

    async def open_order(self, order):
        order_data_manager = self.order_data_manager
        api_manager = self.api_manager

        await order_data_manager.record_event(
            event_params=dict(
                event_name=OrderEventType.OpenRequest,
                date_at=local_now(),
            ),
            order=order,
        )

        exchange_order_id, _ = await api_manager.market_order(
            order, data_manager=order_data_manager
        )

        order = await order_data_manager.save(
            order, save_params=dict(exchange_order_id=exchange_order_id)
        )

        return order
