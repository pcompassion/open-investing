#!/usr/bin/env python3
from asgiref.sync import sync_to_async
from datetime import timedelta
from open_library.time.datetime import now_local
from django.db.models import Q
from django.db import connection

import time
from open_library.data.conversion import ListDataType, ListDataTypeHint, as_list_type
from uuid import uuid4
from django.core.exceptions import ObjectDoesNotExist

from open_investing.order.models.order import Order, Trade, OrderEventEntry
from open_investing.order.const.order import OrderEventName, OrderLifeStage
from open_investing.order.models.composite.composite import CompositeOrder
from open_library.locator.service_locator import ServiceKey
from open_investing.order.const.order import OrderType

from open_library.collections.dict import to_jsonable_python
from open_investing.order.models.order_offset import OrderOffsetRelation
import logging
from open_investing.order.models.order_offset import CompositeOrderOffsetRelation

logger = logging.getLogger(__name__)


class OrderDataManager:
    service_key = ServiceKey(
        service_type="data_manager",
        service_name="database",
        params={"model": "Order.Order"},
    )
    excludes_json = [
        "quantity_multiplier",
        "quantity_order",
        "quantity_exposure",
        "filled_quantity_order",
        "filled_quantity_exposure",
    ]

    async def prepare_order(self, params: dict, save=True):
        plain = {k: v for k, v in params.items() if k in self.excludes_json}
        params_updated = to_jsonable_python(params) | plain

        order = self._unsaved_order(params_updated)

        if save:
            await self.save(order, {})

        return order

    def _unsaved_order(self, params: dict):
        order_type = params["order_type"]

        order_type = OrderType(order_type)
        updated_params = params
        if params.get("id") is None:
            updated_params = params | {"id": uuid4()}

        if order_type.is_single_order:
            order = Order(**updated_params)
            order.set_quantity()
        else:
            order = CompositeOrder(**updated_params)
            order.set_quantity()
        return order

    async def save(self, order, save_params: dict):
        plain = {k: v for k, v in save_params.items() if k in self.excludes_json}
        params = to_jsonable_python(save_params) | plain
        for field, value in params.items():
            setattr(order, field, value)

        await order.asave()

    # async def get(self, filter_params: dict | None):
    #     filter_params = filter_params or {}

    #     order_type = filter_params["order_type"]
    #     order_type = OrderType(order_type)

    #     try:
    #         if order_type.is_single_order:
    #             return await Order.objects.aget(**filter_params)
    #         else:
    #             return await CompositeOrder.objects.aget(**filter_params)
    #     except ObjectDoesNotExist:
    #         return None

    async def get_single_order(self, filter_params: dict | None):
        filter_params = filter_params or {}

        try:
            # order = await Order.objects.aget(**filter_params)
            order = await Order.objects.filter(**filter_params).afirst()

            return order
        except ObjectDoesNotExist:
            return None

    async def get_composite_order(self, filter_params: dict | None):
        filter_params = filter_params or {}

        try:
            # order = await Order.objects.aget(**filter_params)
            order = await CompositeOrder.objects.filter(**filter_params).afirst()

            return order
        except ObjectDoesNotExist:
            return None

    async def handle_exchange_filled_event(self, event_params: dict, order) -> dict:
        parent_order = None
        trade = None
        order_type = OrderType(order.order_type)

        # if order_type.is_single_order:
        #     parent_order = order.parent_order

        fill_quantity_order = event_params["fill_quantity_order"]
        fill_price = event_params["fill_price"]

        params = dict(
            order=order,
            quantity_order=event_params["fill_quantity_order"],
            quantity_multiplier=order.quantity_multiplier,
            price_amount=fill_price.amount,
            currency=fill_price.currency,
            date_at=event_params["date_at"],
        )
        trade = await Trade.objects.acreate(**params)

        if order:
            order.update_fill(fill_quantity_order, fill_price)

        if order.parent_order_id:
            parent_order = await self.get_composite_order(
                filter_params=dict(id=order.parent_order_id)
            )
            await self.handle_exchange_filled_event_for_composite_order(
                event_params, order, parent_order
            )

        offset_result = await self.offset_order(order, fill_quantity_order)

        await order.asave()

        return offset_result

    async def handle_cancel_success_event(self, event_params: dict, order):
        parent_order = order.parent_order

        cancelled_quantity_order = event_params["cancelled_quantity_order"]

        order.subtract_quantity(cancelled_quantity_order)

        if parent_order:
            await self.handle_cancel_success_event_for_composite_order(
                event_params, order, parent_order
            )

        await order.asave()

    async def handle_exchange_filled_event_for_composite_order(
        self, event_params: dict, order, composite_order
    ):
        fill_quantity_order = event_params["fill_quantity_order"]
        fill_price = event_params["fill_price"]

        match composite_order.order_type:
            case OrderType.BestMarketIceberg:
                composite_order.update_fill(fill_quantity_order, fill_price)
                # decision = composite_order.decision
            case OrderType.BestLimitIceberg:
                composite_order.update_fill(fill_quantity_order, fill_price)

            case _:
                pass

        await self.save(composite_order, save_params={})

    async def handle_cancel_success_event_for_composite_order(
        self, event_params: dict, order, composite_order
    ):
        cancelled_quantity_order = event_params["cancelled_quantity_order"]

        match composite_order.order_type:
            case OrderType.BestMarketIceberg:
                composite_order.subtract_quantity(cancelled_quantity_order)
            case _:
                pass

    async def record_event(self, event_params: dict, order=None):
        plain = {k: v for k, v in event_params.items() if k in self.excludes_json}

        event_params_updated = to_jsonable_python(event_params) | plain

        composite_order = None
        trade = None
        event_name = event_params_updated["event_name"]

        if order is not None and not OrderType(order.order_type).is_single_order:
            composite_order = order
            order = None

        order_event = await OrderEventEntry.objects.acreate(
            order=order,
            composite_order=composite_order,
            trade=trade,
            event_name=event_name,
            date_at=event_params["date_at"],
            data=event_params_updated,
        )

        return order_event

    async def filter_single(
        self,
        filter_params: dict,
        field_names: list | None = None,
        return_type: ListDataType = ListDataType.Dataframe,
    ) -> ListDataTypeHint:
        order_type = filter_params.get("order_type", None)

        qs = Order.objects.filter(**filter_params)

        return await as_list_type(qs, return_type, field_names)

    async def filter_composite(
        self,
        filter_params: dict,
        field_names: list | None = None,
        return_type: ListDataType = ListDataType.Dataframe,
    ) -> ListDataTypeHint:
        qs = CompositeOrder.objects.filter(**filter_params)

        return await as_list_type(qs, return_type, field_names)

    async def create_order_offset_relation(
        self, offsetting_order, offsetted_order_id, offset_quantity_order
    ):
        order_offset_relation, _ = await OrderOffsetRelation.objects.aget_or_create(
            offsetting_order=offsetting_order,
            offsetted_order_id=offsetted_order_id,
            defaults={"offset_quantity_order": offset_quantity_order},
        )

    async def create_composite_order_offset_relation(
        self, offsetting_order, offsetted_order_id, offset_quantity_order
    ):
        (
            composite_order_offset_relation,
            _,
        ) = await CompositeOrderOffsetRelation.objects.aget_or_create(
            offsetting_order=offsetting_order,
            offsetted_order_id=offsetted_order_id,
            defaults={"offset_quantity_order": offset_quantity_order},
        )

    async def offset_order(self, offsetting_order, fill_quantity_order) -> dict:
        # TODO: possibly there are many order_offset_relation,
        order_offset_relation = await OrderOffsetRelation.objects.filter(
            offsetting_order=offsetting_order, fully_offsetted=False
        ).afirst()

        offset_result = dict(
            offsetted=False,
            fully_offsetted=False,
            offsetted_order_id=None,
        )

        if order_offset_relation:
            offset_result[
                "offsetted_order_id"
            ] = order_offset_relation.offsetted_order_id
            remaining_quantity_order = order_offset_relation.update_fill(
                fill_quantity_order
            )

            if remaining_quantity_order < 0:
                logger.warning(
                    f"offset_order bigger quantity than requested {remaining_quantity_order}"
                )

            await order_offset_relation.asave()

            offset_result["offsetted"] = True
            offset_result["fully_offsetted"] = order_offset_relation.fully_offsetted

        return offset_result

    async def offset_composite_order(
        self, offsetting_order, fill_quantity_order
    ) -> dict:
        # TODO: possibly there are many order_offset_relation,
        order_offset_relation = (
            await CompositeOrderOffsetRelation.objects.filter(
                offsetting_order=offsetting_order, fully_offsetted=False
            )
            .select_related("offsetted_order")
            .afirst()
        )

        offset_result = dict(
            offsetted=False,
            fully_offsetted=False,
            offsetted_order_id=None,
        )

        if order_offset_relation:
            offset_result[
                "offsetted_order_id"
            ] = order_offset_relation.offsetted_order_id
            remaining_quantity_order = order_offset_relation.update_fill(
                fill_quantity_order
            )

            if remaining_quantity_order < 0:
                logger.warning(
                    f"offset_order bigger quantity than requested {remaining_quantity_order}"
                )

            await order_offset_relation.asave()

            offset_result["offsetted"] = True

            date_at = now_local()

            fully_offsetted = order_offset_relation.fully_offsetted
            offset_result["fully_offsetted"] = fully_offsetted
            offsetted_order = order_offset_relation.offsetted_order

            if fully_offsetted:
                await self.record_event(
                    event_params=dict(
                        event_name=OrderEventName.FullyOffsetted, date_at=date_at
                    ),
                    order=offsetted_order,
                )

                await self.save(
                    offsetting_order,
                    save_params=dict(
                        life_stage=OrderLifeStage.FullyOffsetted,
                        life_stage_updated_at=date_at,
                    ),
                )
                await self.save(
                    offsetted_order,
                    save_params=dict(
                        life_stage=OrderLifeStage.FullyOffsetted,
                        life_stage_updated_at=date_at,
                    ),
                )

        return offset_result

    async def pending_orders(
        self,
        filter_params: dict | None = None,
        exchange_order_id: str | None = None,
        time_window_seconds=3,
    ):
        filter_params = filter_params or {}

        past = now_local() - timedelta(seconds=time_window_seconds)

        filter_params_updated = filter_params | dict(
            life_stage=OrderLifeStage.ExchangeOpenRequest,
            life_stage_updated_at__gte=past,
        )

        q = Q(**filter_params_updated)
        if exchange_order_id:
            q = q | Q(**{"exchange_order_id": exchange_order_id})

        qs = Order.objects.filter(q)

        return await sync_to_async(list)(qs.all())
