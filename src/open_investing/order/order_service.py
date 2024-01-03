#!/usr/bin/env python3


class OrderService:
    # https://chat.openai.com/c/ae7e132e-9005-441c-b0a1-6490b31cb938
    """
    Flow: OrderService does Orchestration

    request: service -> api_manager
    order execution response: api_manager -> pubsub -> service
    service does bookeeping: handle_filled_event
    after bookeeping, send event about update


    """

    def __init__(self, order_data_manager, api_manager):
        self.order_data_manager = order_data_manager
        self.api_manager = api_manager

    async def _open_order(self, order):
        order_data_manager = self.order_data_manager
        api_manager = self.api_manager

        await order_data_manager.record_event(
            event_params=dict(
                event_name=OrderEventType.OpenRequest,
                date_at=local_now(),
            ),
            order=order,
        )

        order_event_broker.subscribe(order.id, self.enqueue_order_event)

        exchange_order_id, _ = await api_manager.market_order(
            order, data_manager=order_data_manager
        )

        order = await order_data_manager.save(
            order, save_params=dict(exchange_order_id=exchange_order_id)
        )

    async def open_order(self, order):
        asyncio.create_task(self._open_order(order))

    async def on_order_event(self, order_info):
        order_exchange_event = order_info["order_exchange_event"]

        order = order_info["order"]

        event_name = order_exchange_event.name

        match event_name:
            case OrderEventName.Filled:
                order_manager.handle_filled_event(
                    order_exchange_event.data, order=order
                )
                order_event = OrderEvent(
                    name=OrderEventName.Filled,
                    data=dict(
                        fill_quantity=data["chevol"],
                        fill_price=data["cheprice"],
                        date_at=combine(data["chedate"], data["chetime"]),
                    ),
                )

                order_event_broker.enqueue_message(
                    order.id,
                    dict(order_event=order_event, order=order),
                )

                # check if filled,
            case _:
                pass

        pass

    async def enqueue_order_event(self, order_event):
        await self.order_event_queue.put(order_event)

    async def run_order_event(self):
        while True:
            order_event = await self.order_event_queue.get()

            await self.on_order_event(order_event)
