#!/usr/bin/env python3


class OrderDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Order.Order"},
    )
    
    async def prepare_order(self, params: dict, save=True):

        order = self._unsaved_order(params)

        if save:
            return await self.save(order, {})
        return order

    def _unsaved_order(self, params: dict):
        order_type = params["order_type"]

        if order_type in SINGLE_ORDER_TYPES:
            return Order(**params)
        else:
            return CompositeOrder(**params)

    async def save(self, order, save_params: dict):
        order_type = order.order_type or save_params["order_type"]

        if order_type in SINGLE_ORDER_TYPES:
            return await order.asave(
                **save_params,
            )
        else:
            return await order.asave(
                **save_params,
            )

    async def get(self, filter_params: dict | None):
        filter_params = filter_params or {}

        order_type = filter_params["order_type"]

        if order_type in SINGLE_ORDER_TYPES:
            return await Order.get(**filter_params)
        else:
            return await CompositeOrder.objects.get(**filter_params)

    async def record_event(self, event_params: dict, order=None):
        composite_order = None
        trade = None

        if order is not None and order.order_type not in SINGLE_ORDER_TYPES:
            composite_order = order
            order = None

        event_name = event_params['event_name']
        match event_name:
            fill_quantity = event_params['fill_quantity']
            fill_price = event_params['fill_price']
            case OrderEventName.Filled:
                params = dict(
                    order=order,
                    quantity = event_params['fill_quantity']
                    price = event_params['fill_price']
                    date_at = event_params['fill_at']
                )
                trade = await Trade.objects.acreate(**params)
                
                order.update_fill(fill_quantity, fill_price)
            case _:
                pass

        order_event = await OrderEvent.objects.acreate(
            order=order,
            composite_order=composite_order,
            trade=trade,
            event_name=event_name,
            date_at=event_params["date_at"],
            data=event_params,
        )

        return order_event

