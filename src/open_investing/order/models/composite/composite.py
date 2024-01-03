#!/usr/bin/env python3


class CompositeOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    order_type = models.CharField(max_length=32)
    data = models.JSONField(default=dict)

    quantity = models.FloatField(default=0)
    filled_quantity = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def update_fill(self):
        # order_type = self.order_type
        # match order_type:
        #     case OrderType.BestMarketIceberg:

        # Update total cost and filled quantity
        new_cost = fill_quantity * fill_price
        self.total_cost += new_cost
        self.filled_quantity += fill_quantity

        # Update average fill price
        if self.filled_quantity > 0:
            self.average_fill_price = self.total_cost / self.filled_quantity
