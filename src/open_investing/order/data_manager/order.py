#!/usr/bin/env python3
from open_investing.order.const.order import SINGLE_ORDER_TYPES
from open_investing.order.models.order import Order, Trade, OrderEvent
from open_investing.order.const.order import OrderEventName
from open_investing.order.models.composite.composite import CompositeOrder
from open_investing.locator.service_locator import ServiceKey
from open_investing.order.const.order import OrderType


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

    async def handle_filled_event(self, event_params: dict, order):
        parent_order = None
        trade = None

        if order.order_type in SINGLE_ORDER_TYPES:
            parent_order = order.parent_order

        fill_quantity = event_params["fill_quantity"]
        fill_price = event_params["fill_price"]

        params = dict(
            order=order,
            quantity=event_params["fill_quantity"],
            price=event_params["fill_price"],
            date_at=event_params["fill_at"],
        )
        trade = await Trade.objects.acreate(**params)

        if order:
            order.update_fill(fill_quantity, fill_price)

        if parent_order:
            await self.handle_filled_event_for_composite_order(
                event_params, order, parent_order
            )

        await order.asave()

    async def handle_cancel_success_event(self, event_params: dict, order):
        parent_order = order.parent_order

        cancelled_quantity = event_params["cancelled_quantity"]

        order.subtract_quantity(cancelled_quantity)

        if parent_order:
            await self.handle_cancel_success_event_for_composite_order(
                event_params, order, parent_order
            )

        await order.asave()

    async def handle_filled_event_for_composite_order(
        self, event_params: dict, order, composite_order
    ):
        fill_quantity = event_params["fill_quantity"]
        fill_price = event_params["fill_price"]

        match composite_order.order_type:
            case OrderType.BestMarketIceberg:
                composite_order.update(fill_quantity, fill_price)
            case _:
                pass

    async def handle_cancel_success_event_for_composite_order(
        self, event_params: dict, order, composite_order
    ):
        cancelled_quantity = event_params["cancelled_quantity"]

        match composite_order.order_type:
            case OrderType.BestMarketIceberg:
                composite_order.subtract_quantity(cancelled_quantity)
            case _:
                pass

    async def handle_event(self, event_params: dict, order=None):
        event_name = event_params["event_name"]
        match event_name:
            case OrderEventName.ExchangeFilled:
                await self.handle_filled_event(event_params, order)

            case OrderEventName.ExchangeCancelSuccess:
                await self.handle_cancel_success_event(event_params, order)
            case _:
                pass

        await self.record_event(event_params, order=order)

    async def record_event(self, event_params: dict, order=None):
        composite_order = None
        trade = None
        event_name = event_params["event_name"]

        if order is not None and order.order_type not in SINGLE_ORDER_TYPES:
            composite_order = order
            order = None

        order_event = await OrderEvent.objects.acreate(
            order=order,
            composite_order=composite_order,
            trade=trade,
            event_name=event_name,
            date_at=event_params["date_at"],
            data=event_params,
        )

        return order_event
