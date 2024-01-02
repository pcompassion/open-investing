#!/usr/bin/env python3


class OrderDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Order.Order"},
    )

    def unsaved_order(self, params: dict):
        return Order(**params)

    async def save(self, order, save_params: dict):
        return await order.asave(
            **save_params,
        )

    async def get_order(self, exchange_order_id: str):
        return await order.aget(exchange_order_id=exchange_order_id)
