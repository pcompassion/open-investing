#!/usr/bin/env python3
from django.db import models


class OrderOffsetRelation(models.Model):
    offsetting_order = models.ForeignKey(
        "order.Order", related_name="_offsetted_by_me", on_delete=models.CASCADE
    )
    offsetted_order = models.ForeignKey(
        "order.Order", related_name="_offsetting_me", on_delete=models.CASCADE
    )
    offset_quantity = models.PositiveIntegerField(
        default=0
    )  # Field for offset quantity
    filled_quantity = models.PositiveIntegerField(default=0)

    fully_offsetted = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def update_fill(self, fill_quantity):
        self.filled_quantity += fill_quantity

        remaining_quantity = self.offset_quantity - self.filled_quantity
        self.filled_quantity = min(self.offset_quantity, self.filled_quantity)

        if self.filled_quantity == self.offset_quantity:
            self.fully_offsetted = True

        return remaining_quantity
