#!/usr/bin/env python3
from django.db import models
from decimal import Decimal


class OrderOffsetRelation(models.Model):
    offsetting_order = models.ForeignKey(
        "order.Order", related_name="_offsetted_by_me", on_delete=models.CASCADE
    )
    offsetted_order = models.ForeignKey(
        "order.Order", related_name="_offsetting_me", on_delete=models.CASCADE
    )
    offset_quantity_order = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    filled_quantity_order = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )

    quantity_multiplier = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("1")
    )

    fully_offsetted = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def update_fill(self, fill_quantity_order):
        self.filled_quantity_order += fill_quantity_order

        remaining_quantity_order = (
            self.offset_quantity_order - self.filled_quantity_order
        )
        self.filled_quantity_order = min(
            self.offset_quantity_order, self.filled_quantity_order
        )

        if self.filled_quantity_order == self.offset_quantity_order:
            self.fully_offsetted = True

        return remaining_quantity_order


class CompositeOrderOffsetRelation(models.Model):
    offsetting_order = models.ForeignKey(
        "order.CompositeOrder",
        related_name="_offsetted_by_me",
        on_delete=models.CASCADE,
    )
    offsetted_order = models.ForeignKey(
        "order.CompositeOrder", related_name="_offsetting_me", on_delete=models.CASCADE
    )
    offset_quantity_order = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0")
    )
    filled_quantity_order = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0")
    )

    quantity_multiplier = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("1")
    )

    fully_offsetted = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def update_fill(self, fill_quantity_order):
        self.filled_quantity_order += fill_quantity_order

        remaining_quantity_order = (
            self.offset_quantity_order - self.filled_quantity_order
        )
        self.filled_quantity_order = min(
            self.offset_quantity_order, self.filled_quantity_order
        )

        if self.filled_quantity_order == self.offset_quantity_order:
            self.fully_offsetted = True

        return remaining_quantity_order
