#!/usr/bin/env python3
from open_investing.task.task_command import SubCommand, TaskCommand
from open_investing.order.const.order import OrderCommandName
from open_investing.task_spec.task_spec_handler_registry import TaskSpecHandlerRegistry
import asyncio
from open_investing.strategy.models.decision import Decision
from open_investing.locator.service_locator import ServiceKey
from typing import ClassVar
from open_investing.task_spec.decision.decison import DecisionSpec, DecisionHandler


class DeltaHedgeDecisionSpec(DecisionSpec):
    spec_type_name_classvar: ClassVar[str] = "decision.delta_hedge"
    spec_type_name: str = spec_type_name_classvar

    security_code_leader: str
    security_code_follower: str
    leader_follower_ratio: float


@TaskSpecHandlerRegistry.register_class
class DeltaHedgeDecisionHandler(DecisionHandler):
    task_spec_cls = DeltaHedgeDecisionSpec

    def __init__(self, decision_spec: DecisionSpec) -> None:
        super().__init__(decision_spec)

        self.open_decisions: list[Decision] = []

    async def on_decision(self, decision_info):
        decision_spec = decision_info["task_spec"]
        order_task_dispatcher = self.order_task_dispatcher

        decision_id = decision_spec.decision_id

        decision_data_manager = self.decision_data_manager
        decision: Decision = await decision_data_manager.get(id=decision_id)

        command = decision_info["command"]

        if command.name == "start":
            await decision_data_manager.set_started(decision)

            order_spec_dict = self.base_spec_dict | dict(
                spec_type_name="order.best_market_iceberg",
                time_interval_second=10,
                split=5,
            )

            order_command = TaskCommand(
                name="command", sub_command=SubCommand(name=OrderCommandName.Open)
            )

            await order_task_dispatcher.dispatch_task(order_spec_dict, order_command)

    async def run(self):
        while True:
            # while not self.command_queue.empty():
            decision_info = await self.command_queue.get()

            await self.on_decision(decision_info)
