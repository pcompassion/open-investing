#!/usr/bin/env python3
from typing import Dict, Type
from open_investing.market_event.market_event import MarketEventSpec, IMarketEventSource
from open_investing.task_spec.task_spec import TaskSpec


class TaskSpecHandlerRegistry:
    task_spec_handler_classes: Dict[str, Type[TaskSpecHandler]] = {}

    @classmethod
    def register_class(cls, target_cls: Type[TaskSpecHandler]):
        spec_type_name = target_cls.task_spec_cls.spec_type_name

        if spec_type_name in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {task_spec_name} is already registered")

        cls.task_spec_handler_classes[task_spec_name] = target_cls

    @classmethod
    def create_handler_instance(cls, task_spec: TaskSpec):
        task_spec_cls = type(task_spec)
        task_spec_name = task_spec_cls.spec_type_name

        if task_spec_name not in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {task_spec_name} is not registered")

        task_spec_handler_cls = cls.task_spec_handler_classes[task_spec_name]

        return task_spec_handler_cls(task_spec)
