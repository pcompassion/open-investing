#!/usr/bin/env python3
from open_library.data.conversion import ListDataType
from open_investing.task.task import Task
from open_investing.strategy.const.decision import (
    DecisionCommandName,
    DecisionLifeStage,
)
from open_investing.task_spec.order.order import OrderCommand, OrderTaskCommand
from open_investing.task.task_command import SubCommand, TaskCommand
from open_investing.order.const.order import OrderCommandName, OrderSide, OrderType
from open_investing.task_spec.task_spec_handler_registry import TaskSpecHandlerRegistry
import asyncio
from open_investing.strategy.models.decision import Decision
from open_library.locator.service_locator import ServiceKey
from typing import ClassVar
from open_investing.task_spec.decision.decison import DecisionSpec, DecisionHandler
from open_investing.order.const.order import OrderEventName
import logging

logger = logging.getLogger(__name__)


class DeltaHedgeDecisionSpec(DecisionSpec):
    spec_type_name_classvar: ClassVar[str] = "decision.delta_hedge"
    spec_type_name: str = spec_type_name_classvar

    leader_security_code: str
    follower_security_code: str
    leader_follower_ratio: float
    leader_quantity: float


@TaskSpecHandlerRegistry.register_class
class DeltaHedgeDecisionHandler(DecisionHandler):
    task_spec_cls = DeltaHedgeDecisionSpec

    def __init__(self, decision_spec: DecisionSpec) -> None:
        super().__init__(decision_spec)

        self.open_decisions: list[Decision] = []
        self.cancel_events = {}

        self.tasks = dict(
            run_strategy=Task("run_decision", self.run_decision()),
        )
        self.strategy_session_id = self.decision_spec.strategy_session_id

    async def on_decision(self, decision_info):
        decision_spec = decision_info["task_spec"]
        order_task_dispatcher = self.order_task_dispatcher

        decision_id = decision_spec.decision_id

        decision_data_manager = self.decision_data_manager
        decision: Decision = await decision_data_manager.get(
            filter_params=dict(id=decision_id)
        )

        command = decision_info["command"]

        match command.name:
            case DecisionCommandName.Start:
                await decision_data_manager.set_started(decision)

                # for test
                # order_spec_dict = self.base_spec_dict | dict(
                #     spec_type_name="order.best_market_iceberg",
                #     time_interval_second=10,
                #     split=5,
                #     security_code=self.decision_spec.leader_security_code,
                #     quantity=self.decision_spec.leader_quantity,
                #     order_id=None,
                #     parent_order_id=None,
                # )
                order_spec_dict = self.base_spec_dict | dict(
                    spec_type_name=OrderType.BestLimitIceberg,
                    max_tick_diff=5,
                    tick_size=0.25,
                    order_side=OrderSide.Sell,
                    security_code=self.decision_spec.leader_security_code,
                    quantity=self.decision_spec.leader_quantity,
                    order_id=None,
                    parent_order_id=None,
                )

                order_command = OrderTaskCommand(
                    name="command",
                    order_command=OrderCommand(name=OrderCommandName.Open),
                )

                await order_task_dispatcher.dispatch_task(
                    order_spec_dict, order_command
                )
                logger.info("on_decision ended")
            case DecisionCommandName.Close:
                # TODO: close all orders
                # maybe keep ongoing_orders to avoid db read

                # TODO: should close remaining as well
                # TODO: should stop all active order tasks
                order_command = OrderTaskCommand(
                    name="command",
                    order_command=OrderCommand(name=OrderCommandName.Close),
                )

                order_data_manager = self.order_data_manager
                orders_single = await order_data_manager.filter(
                    filter_params=dict(strategy_session_id=self.strategy_session_id),
                    return_type=ListDataType.List,
                )
                orders_composite = await order_data_manager.filter(
                    filter_params=dict(
                        strategy_session_id=self.strategy_session_id,
                        order_type=OrderType.BestLimitIceberg,
                    ),
                    return_type=ListDataType.List,
                )

                orders = orders_single + orders_composite

                for order in orders:
                    order_spec_dict = self.base_spec_dict | dict(
                        spec_type_name=order.order_type,
                        strategy_name=order.strategy_session.strategy_name,
                        strategy_session_id=order.strategy_session_id,
                        order_id=order.id,
                        order_side=OrderSide(order.side).opposite,
                        parent_order_id=None,
                    )

                    await order_task_dispatcher.dispatch_task(
                        order_spec_dict, order_command
                    )

    async def run_decision(self):
        while True:
            # while not self.command_queue.empty():
            try:
                decision_info = await self.command_queue.get()

                await self.on_decision(decision_info)
            except Exception as e:
                logger.info("e")

    async def start_tasks(self):
        self.running = True
        for k, task in self.tasks.items():
            await task.start()

    async def on_order_event(self, order_info):
        order_event = order_info["event"]
        logger.info(f"on_order_event: {order_event}")

        order = order_info["order"]

        if order.strategy_session_id != self.strategy_session_id:
            return

        event_name = order_event.name

        match event_name:
            case OrderEventName.Filled:
                # TODO: better check tighter condition
                fill_quantity = order_event.data["fill_quantity"]

                if order.security_code == self.decision_spec.leader_security_code:
                    quantity = fill_quantity * self.decision_spec.leader_follower_ratio

                    order_spec_dict = self.base_spec_dict | dict(
                        spec_type_name=OrderType.Market,
                        security_code=self.decision_spec.follower_security_code,
                        quantity=quantity,
                        order_side=OrderSide.Sell,
                        order_id=None,
                        parent_order_id=None,
                    )

                    order_command = OrderTaskCommand(
                        name="command",
                        order_command=OrderCommand(name=OrderCommandName.Open),
                    )
                    order_task_dispatcher = self.order_task_dispatcher

                    await order_task_dispatcher.dispatch_task(
                        order_spec_dict, order_command
                    )

                elif order.security_code == self.decision_spec.follower_security_code:
                    decision_fill_quantity = (
                        fill_quantity / self.decision_spec.leader_follower_ratio
                    )

                    # actually decision filled

                    decision = order.decision
                    decision.update_fill(decision_fill_quantity)

                    # TODO: maybe notify/update strategy

                    save_params = {}
                    if decision.is_fullfilled():
                        save_params["life_stage"] = DecisionLifeStage.Fullfilled
                    decision_data_manager = self.decision_data_manager
                    await decision_data_manager.save(decision, save_params=save_params)

            case OrderEventName.CancelSuccess:
                order_id = order.id

                event = self.cancel_events.get(order_id)
                if event:
                    event.set()
                    del self.cancel_events[event]
            case _:
                pass

        pass
