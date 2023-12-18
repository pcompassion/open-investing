#!/usr/bin/env python3
from typing import Dict
from open_investing.market_event.market_event import MarketEventSpec, IMarketEventSource


class TaskSpecHandlerRegistry:
    task_spec_handler_classes: Dict[TaskSpec, TaskSpecHandler] = {}

    @classmethod
    def register_class(cls, task_spec_class: TaskSpec, target_cls):
        if task_spec_class in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {task_spec_class} is already registered")

        cls.task_spec_handler_classes[task_spec_class] = target_cls

    @classmethod
    def create_instance(cls, task_spec: TaskSpec):
        task_spec_cls = type(task_spec)

        if task_spec_cls not in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {task_spec} is not registered")

        task_spec_handler_cls = cls.task_spec_handler_classes[task_spec_cls]
