#!/usr/bin/env python3
import asyncio
from open_investing.locator.service_locator import ServiceKey
from typing import ClassVar
from open_investing.task_spec.order.order import OrderSpec
from open_investing.order.models.order import Order
from open_investing.task_spec.order.order import OrderAgent


class BestMarketIcebergOrderSpec(OrderSpec):
    spec_type_name_classvar: ClassVar[str] = "order.best_market_iceberg_order"
    spec_type_name: str = spec_type_name_classvar

    time_interval: float
    split: int


class BestMarketIcebergOrderAgent(OrderAgent):
    task_spec_cls = BestMarketIcebergOrderSpec

    order_type = OrderType.BestMarketIceberg

    """
      - 주문형태2-2. 지정가 주문 -최유리 지정가   
        - 상황: 어느 정도 시급한 상황이지만 market impact를 줄이면서 유리하게 매매하고 싶은 경우          
        - 목표 수량(N)만 정해진 지정가  
        - 목표수량의 1/k 만큼 t초 간격으로 최유리호가에 주문하되, 부분 체결되는    경우 남은 수량은 취소후 재 주문  
        - 예) 목표 수량 100개(N=100)를 매수하는 경우, 총수량을 k개로 나눠서 market impact를 줄여서 체결시킴. 최유리호가에 10개씩 주문함. t초동안 체결되기를 기다린후, 전량 체결되는 경우는 다음 10개주문. 부분 체결 되는 경우 잔량은 취소후 다음 10개 주문. 반복하여 목표수량 N개가 모두 체결되기까지 반복  
    
    
    def 최유리_지정가(목표수량=N, time_interval=t초, split=k):
      총체결수량=0
      while(총체결수량<N):
        체결량=0
        최유리지정가주문(n=min[N/k, N-총체결수량])
        wait(t초):
          총체결수량=총체결수량+체결량
        if 체결량<n:  #일부체결시
          pending중인 주문(n-체결량) 취소

        총체결수량=총체결수량+체결량
    

    """

    def __init__(self, order_spec):
        super().__init__(order_spec)

    async def run_order(self, order_spec, order):
        time_interval = order_spec.time_interval
        split = order_spec.split
        security_code = order_spec.security_code
        quantity = order_spec.quantity

        filled_quantity = order.filled_quantity

        while filled_quantity < quantity:
            order_spec = self.order_spec

            quantity_partial = min(quantity / split, quantity - filled_quantity)

            order_spec_dict = {
                "spec_type_name": "order.market_order",
                "strategy_name": order_spec.strategy_name,
                "strategy_session_id": order_spec.strategy_session_id,
                "security_code": security_code,
                "quantity": quantity_partial,
            }

            # task_dispatcher.subscribe(
            #     order_spec_dict, subscription_key, ListenerType.ChannelGroup
            # )

            command_dict = dict(name=OrderCommandName.Open)

            command = OrderCommand(**command_dict)
            await task_dispatcher.dispatch_task(order_spec_dict, command)
            # need order_id (to cancel it)
            # need filled event handling

            await asyncio.sleep(time_interval)

            filled_quantity_new = order.filled_quantity

            if filled_quantity_new < quantity_partial:
                command_dict = dict(name=OrderCommandName.Cancel)

                command = OrderCommand(**command_dict)

                # need to add order_id to order_spec_dict
                # need to subscribe for cancel event
                await task_dispatcher.dispatch_task(order_spec_dict, command)

    async def on_order_command(self, order_info):
        order_spec = order_info["task_spec"]
        order_id = order_spec.order_id

        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Order.Order"},
        )
        order_manager = self.services[service_key]

        exchange_service_key = self.task_spec.get_service_key(
            name="exchange_api_manager"
        )

        api_manager = self.services[exchange_service_key]

        if order_id:
            order = await order_manager.get(
                filter_params=dict(id=order_id, order_type=self.order_type)
            )
        else:
            order = order_data_manager.prepare_order(
                params=dict(
                    quantity=order_spec.quantity,
                    order_type=self.order_type,
                    data=dict(
                        security_code=order_spec.security_code,
                        side=OrderSide.Buy,
                        time_interval=order_spec.time_interval,
                        split=order_spec.split,
                    ),
                )
            )

        command = order_info["command"]

        if command.name == "open":
            await api_manager.market_order(order)

    async def on_order_event(self, order_event):
        pass
