#!/usr/bin/env python3
from open_investing.strategy.models.decision import Decision
from open_investing.locator.service_locator import ServiceKey
from typing import ClassVar
from open_investing.task_spec.decision.decison import DecisionSpec, DecisionHandler


class DeltaHedgeSpec(DecisionSpec):
    spec_type_name_classvar: ClassVar[str] = "decision.delta_hedge"
    spec_type_name: str = spec_type_name_classvar
    
    security_code_leader: str
    security_code_follower: str
    leader_follower_ratio: float


@TaskSpecHandlerRegistry.register_class
class DeltaHedgeDecisionHandler(DecisionHandler):
    task_spec_cls = DeltaHedgeSpec

    def __init__(self, decision_spec: DecisionSpec) -> None:
        super().__init__(decision_spec)
        self.command_queue = asyncio.Queue()

        self.open_decisions: list[Decision] = []

    async def enqueue_decision_command(self, decision_info):
        await self.command_queue.put(decision_info)

    async def on_decision(self, decision_info):

        decision_spec = decision_info["task_spec"]

        decision_id = decision_spec.decision_id
        
        service_key = ServiceKey(
            service_type="data_manager",
            service_name="database",
            params={"model": "Strategy.Decision"},
        )
        decision_manager = self.services[service_key]

        decision: Decision = await decision_manager.get(id=decision_id)

        command = decision_info["command"]

        if command.name == "start":        

            await decision_manager.set_started(decision)

    async def run(self):
        while True:
            # while not self.command_queue.empty():
            decision_info = await self.command_queue.get()

            await self.on_decision(decision_info)
