#!/usr/bin/env python3
from decimal import Decimal
from open_investing.event_spec.event_spec import OrderEventSpec
from uuid import uuid4
from open_library.data.conversion import ListDataType
from open_investing.task.task import Task
from open_investing.strategy.const.decision import (
    DecisionCommandName,
    DecisionLifeStage,
)
from open_investing.task_spec.order.order import OrderCommand, OrderTaskCommand
from open_investing.task.task_command import SubCommand, TaskCommand
from open_investing.order.const.order import (
    OrderCommandName,
    OrderLifeStage,
    OrderSide,
    OrderType,
)
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
    leader_follower_ratio: Decimal

    leader_quantity_exposure: Decimal
    leader_multiplier: Decimal
    follower_multiplier: Decimal
    max_tick_diff: int = 5


@TaskSpecHandlerRegistry.register_class
class DeltaHedgeDecisionHandler(DecisionHandler):
    task_spec_cls = DeltaHedgeDecisionSpec

    def __init__(self, decision_spec: DecisionSpec) -> None:
        super().__init__(decision_spec)

        self.open_decisions: list[Decision] = []
        self.cancel_events = {}

        self.tasks = dict(
            run_strategy=Task("run_decision", self.run_decision()),
            run_order_event=Task("run_order_event", self.run_order_event()),
        )
        self.strategy_session_id = self.decision_spec.strategy_session_id
        self.order_ids = []
        self.decision_specs = {}

    async def on_decision(self, decision_info):
        decision_spec = decision_info["task_spec"]
        command = decision_info["command"]

        logger.info(f"on_decision: {decision_spec}, command: {command}")
        order_task_dispatcher = self.order_task_dispatcher

        decision_id = decision_spec.decision_id
        self.decision_specs[decision_id] = decision_spec

        decision_data_manager = self.decision_data_manager
        decision: Decision = await decision_data_manager.get(
            filter_params=dict(id=decision_id)
        )

        match command.name:
            case DecisionCommandName.Start:
                await decision_data_manager.set_started(decision)

                order_id = uuid4()
                self.order_ids.append(order_id)

                order_event_spec = OrderEventSpec(order_id=order_id)
                self.order_event_broker.subscribe(
                    order_event_spec, self.enqueue_order_event
                )

                order_spec_dict = self.base_spec_dict | dict(
                    spec_type_name=OrderType.BestLimitIceberg,
                    max_tick_diff=decision_spec.max_tick_diff,
                    tick_size=Decimal("0.01"),
                    order_side=OrderSide.Sell,
                    security_code=decision_spec.leader_security_code,
                    quantity_exposure=decision_spec.leader_quantity_exposure,
                    quantity_multiplier=decision_spec.leader_multiplier,
                    strategy_session_id=decision_spec.strategy_session_id,
                    decision_id=decision_id,
                    order_id=order_id,
                    parent_order_id=None,
                )

                order_command = OrderTaskCommand(
                    name="command",
                    order_command=OrderCommand(name=OrderCommandName.Open),
                )

                await order_task_dispatcher.dispatch_task(
                    order_spec_dict, order_command
                )
                # logger.info("on_decision ended")
            case DecisionCommandName.Offset:
                # TODO: close all orders
                # maybe keep ongoing_orders to avoid db read

                # TODO: should close remaining as well
                # TODO: should stop all active order tasks
                order_command = OrderTaskCommand(
                    name="command",
                    order_command=OrderCommand(name=OrderCommandName.Offset),
                )

                order_data_manager = self.order_data_manager
                # orders_single = await order_data_manager.filter(
                #     filter_params=dict(strategy_session_id=self.strategy_session_id),
                #     return_type=ListDataType.List,
                # )

                offsetted_decision_id = decision_spec.offsetted_decision_id
                orders_composite = await order_data_manager.filter_composite(
                    filter_params=dict(
                        decision_id=offsetted_decision_id,
                        # strategy_session_id=self.strategy_session_id,
                        order_type=OrderType.BestLimitIceberg,
                        is_offset=False,
                        life_stage__in=[
                            OrderLifeStage.Undefined,
                            OrderLifeStage.Opened,
                            OrderLifeStage.Fullfilled,
                        ],
                    ),
                    return_type=ListDataType.List,
                )

                # orders = orders_single + orders_composite

                orders = orders_composite

                for order in orders:
                    order_id = uuid4()

                    decision = order.decision
                    security_code = decision.decision_params.get("leader_security_code")

                    order_spec_dict = self.base_spec_dict | dict(
                        spec_type_name=order.order_type,
                        decision_id=decision_spec.decision_id,
                        max_tick_diff=decision_spec.max_tick_diff,
                        tick_size=Decimal("0.01"),
                        strategy_session_id=order.strategy_session_id,
                        order_side=OrderSide.Buy,
                        security_code=security_code,
                        quantity_exposure=order.filled_quantity_exposure,
                        quantity_multiplier=order.quantity_multiplier,
                        offsetted_order_id=order.id,
                        order_id=order_id,
                        parent_order_id=None,
                        is_offset=True,
                    )

                    order_event_spec = OrderEventSpec(order_id=order_id)
                    self.order_event_broker.subscribe(
                        order_event_spec, self.enqueue_order_event
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
                logger.info(f"run_decision: {e}")

    async def start_tasks(self):
        self.running = True
        for k, task in self.tasks.items():
            await task.start()

    async def on_order_event(self, order_info):
        event_spec = order_info["event_spec"]
        order = order_info["order"]
        data = order_info.get("data")

        logger.info(f"on_order_event: {event_spec}, data: {data}")

        if order.strategy_session_id != self.strategy_session_id:
            return

        date_at = data.get("date_at")

        event_name = event_spec.name
        decision = order.decision

        decision_id = order.decision_id

        if decision_id in self.decision_specs:
            decision_spec = self.decision_specs[decision_id]
        else:
            logger.warning(f"no decision_spec for decision_id: {decision_id}")
            return

        match event_name:
            case OrderEventName.Filled:
                # TODO: better check tighter condition

                if order.security_code == decision_spec.leader_security_code:
                    # composite_order = order.parent_order
                    # # if opening order, we wait for filled
                    # # when offsetting order, immediate followup
                    # if order.is_filled() or composite_order.is_offset:
                    follow_condition_met = False
                    fill_quantity_order = 0
                    if order.is_offset:
                        fill_quantity_order = data["fill_quantity_order"]
                        follow_condition_met = True
                    else:
                        if order.is_filled():
                            fill_quantity_order = order.filled_quantity_order
                            follow_condition_met = True

                    if follow_condition_met:
                        # TODO: min quantity is 1 ?
                        MIN_QUANTITY = Decimal("1")
                        quantity_order = max(
                            fill_quantity_order
                            * decision_spec.leader_follower_ratio
                            * decision_spec.leader_multiplier
                            / decision_spec.follower_multiplier,
                            MIN_QUANTITY,
                        )
                        quantity_order = Decimal(int(quantity_order))

                        quantity_exposure = (
                            quantity_order * decision_spec.follower_multiplier
                        )

                        leader_follower_ratio = (
                            quantity_order
                            / (fill_quantity_order * decision_spec.leader_multiplier)
                            * decision_spec.follower_multiplier
                        )

                        leader_quantity_order = fill_quantity_order

                        order_id = uuid4()

                        order_spec_dict = self.base_spec_dict | dict(
                            spec_type_name=OrderType.Market,
                            decision_id=decision_spec.decision_id,
                            security_code=decision_spec.follower_security_code,
                            quantity_exposure=quantity_exposure,
                            quantity_multiplier=decision_spec.follower_multiplier,
                            order_side=OrderSide(order.side),
                            strategy_session_id=decision_spec.strategy_session_id,  # TODO: shouldnt be neccessary
                            order_id=order_id,
                            parent_order_id=order.parent_order_id,
                            is_offset=order.is_offset,
                            leader_quantity_order=leader_quantity_order,
                            leader_follower_ratio=leader_follower_ratio,
                        )

                        order_event_spec = OrderEventSpec(order_id=order_id)
                        self.order_event_broker.subscribe(
                            order_event_spec, self.enqueue_order_event
                        )

                        order_command = OrderTaskCommand(
                            name="command",
                            order_command=OrderCommand(name=OrderCommandName.Open),
                        )
                        order_task_dispatcher = self.order_task_dispatcher

                        await order_task_dispatcher.dispatch_task(
                            order_spec_dict, order_command
                        )
                    if not DecisionLifeStage(decision.life_stage).has_opened:
                        save_params = dict(
                            life_stage=DecisionLifeStage.Opened,
                            life_stage_updated_at=date_at,
                        )
                        decision_data_manager = self.decision_data_manager
                        await decision_data_manager.save(
                            decision, save_params=save_params
                        )

                elif (
                    order.security_code == decision_spec.follower_security_code
                    and order.order_type == OrderType.Market
                ):
                    fill_quantity_order = data["fill_quantity_order"]

                    # leader_fill_quantity_order = (
                    #     fill_quantity_order
                    #     * decision_spec.follower_multiplier
                    #     / order.leader_follower_ratio
                    #     / decision_spec.leader_multiplier
                    # )

                    leader_fill_quantity_order = order.leader_quantity_order
                    leader_follower_ratio = order.leader_follower_ratio
                    # assert (
                    #     leader_fill_quantity_order
                    #     == leader_follower_ratio * fill_quantity_order
                    # )

                    # leader_fill_quantity_order = (
                    #     fill_quantity_order / decision_spec.leader_follower_ratio
                    # )

                    order_data_manager = self.order_data_manager
                    composite_order = await order_data_manager.get_composite_order(
                        filter_params=dict(id=order.parent_order_id)
                    )
                    (
                        offset_result,
                        order_offset_relation,
                    ) = await order_data_manager.offset_composite_order(
                        composite_order, leader_fill_quantity_order
                    )

                    # actually decision filled

                    decision.update_fill(leader_fill_quantity_order)

                    logger.info(
                        f"decision_id: {decision.id},quantity_order: {decision.quantity_order}, filled_quantity_order: {decision.filled_quantity_order}"
                    )

                    # TODO: maybe notify/update strategy

                    save_params = {}
                    if decision.is_fullfilled():
                        save_params["life_stage"] = DecisionLifeStage.Fullfilled
                        save_params["life_stage_updated_at"] = date_at
                        logger.info(f"decision fullfilled: {decision.id}")

                    decision_data_manager = self.decision_data_manager
                    await decision_data_manager.save(decision, save_params=save_params)

                    if offset_result.get("fully_offsetted"):
                        offsetted_order = order_offset_relation.offsetted_order
                        offset_save_params = dict(
                            life_stage=OrderLifeStage.FullyOffsetted,
                            life_stage_updated_at=date_at,
                        )
                        await order_data_manager.save(
                            order, save_params=offset_save_params
                        )

                        offsetted_decision = await decision_data_manager.get(
                            filter_params=dict(id=offsetted_order.decision_id)
                        )

                        await decision_data_manager.save(
                            offsetted_decision,
                            save_params=dict(
                                life_stage=DecisionLifeStage.FullyOffsetted,
                                life_stage_updated_at=date_at,
                            ),
                        )

            case OrderEventName.CancelSuccess:
                order_id = order.id

                event = self.cancel_events.get(order_id)
                if event:
                    event.set()
                    del self.cancel_events[event]

            case OrderEventName.ExchangeOpenRequest | OrderEventName.ExchangeOpenSuccess | OrderEventName.ExchangeOpenFailure:
                if order.security_code == decision_spec.leader_security_code:
                    save_params = dict(
                        life_stage=event_name,
                        life_stage_updated_at=date_at,
                    )
                    decision_data_manager = self.decision_data_manager
                    await decision_data_manager.save(decision, save_params=save_params)

            case _:
                pass

        pass
