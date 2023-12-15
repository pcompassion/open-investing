#!/usr/bin/env python3

import asyncio
from decimal import Decimal, ROUND_HALF_UP

from open_investing.order.const.order import (
    OrderDirection,
    OrderPriceType,
)



class LimitOrderAgent:
    def __init__(self, api_instance=None):
        self.order_details = None
        self.api = api_instance

    async def run(self):
        while self.is_active:
            # Create a snapshot at the start of each iteration
            current_order_details = self.shared_order_details.copy()

            # Use current_order_details throughout this iteration
            # ...

            await asyncio.sleep(1)  # Non-blocking wait

    async def place_order(
        self,
        tr_code,
        security_code: str,
        order_quantity: int,
        price: Decimal,
        order_direction: OrderDirection,
        order_price_type: OrderPriceType = OrderPriceType.LIMIT,
    ):
        api = self.api
        price = Decimal(str(price))
        price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


        send_data = api.get_send_data(
            tr_code=tr_code,
            security_code=security_code,
            order_quantity=order_quantity,
            order_price=float(price),
            order_direction=order_direction,
            order_price_type=order_price_type,
        )

        api_response = await api.order_action(
            tr_code,
            body_block=send_data,
        )

        return api_response


    def update_order_details(self, new_details):
        # Update the shared_order_details directly
        self.shared_order_details = new_details.copy()

# Usage
async def main():
    initial_order_details = # ...
    order_task = AsyncOrderTask(initial_order_details)
    task = asyncio.create_task(order_task.run())

    # Other tasks
    # ...

    # Update order details without awaiting
    new_order_details = # ...
    order_task.update_order_details(new_order_details)

asyncio.run(main())
