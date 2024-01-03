class MarketOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = "order.market_order"
    spec_type_name: str = spec_type_name_classvar


class MarketOrderAgent(OrderAgent):
    task_spec_cls = MarketOrderSpec

    order_type = OrderType.Market
    order_price_type = OrderPriceType.Market

    def __init__(self, order_spec):
        super().__init__(order_spec)

        service_key = self.task_spec.get_service_key(name="exchange_api_manager")
        self.api_manager = self.services[service_key]

    async def on_order_command(self, order_info):
        order_spec = order_info["task_spec"]
        order_id = order_spec.order_id

        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Order.Order"},
        )
        order_data_manager = self.services[service_key]

        if order_id:
            order = await order_data_manager.get(
                filter_params=dict(id=order_id, order_type=self.order_type)
            )
        else:
            order = order_data_manager.prepare_order(
                params=dict(
                    quantity=order_spec.quantity,
                    order_type=self.order_type,
                    security_code=order_spec.security_code,
                    side=OrderSide.Buy,
                    compsoite_order_id=order_spec.composite_order_id,
                    order_price_type=self.order_price_type,
                )
            )

        command = order_info["command"]

        if command.name == OrderCommandName.Open:
            order_event_broker = self.order_event_broker

            order_event_broker.subscribe(order.id, self.enqueue_order_event)

            await order_service.open_order(order)

    async def on_order_exchange_event(self, order_info):
        order_exchange_event = order_info["order_exchange_event"]

        order = order_info["order"]

        event_name = order_exchange_event.name

        match event_name:
            case OrderEventName.Filled:
                order_manager.record_event(order_exchange_event.data, order=order)
                # check if filled,
            case _:
                pass

        pass
