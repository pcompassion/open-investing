#!/usr/bin/env python3
from typing import Dict, Type
from open_investing.market_event.market_event import MarketEventSpec, IMarketEventSource
from open_investing.task_spec.task_spec import TaskSpec


class TaskSpecHandlerRegistry:
    task_spec_handler_classes: Dict[str, Type[TaskSpecHandler]] = {}

    @classmethod
    def register_handler_class(cls, target_cls: Type[TaskSpecHandler]):
        spec_type
        if task_spec_class in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {task_spec_class} is already registered")

        cls.task_spec_handler_classes[task_spec_class] = target_cls

    @classmethod
    def create_instance(cls, task_spec: TaskSpec):
        task_spec_cls = type(task_spec)

        if task_spec_cls not in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {task_spec} is not registered")

        task_spec_handler_cls = cls.task_spec_handler_classes[task_spec_cls]

        return task_spec_handler_cls(task_spec)
