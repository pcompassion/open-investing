#!/usr/bin/env python3
from typing import Dict, Type
from functools import singledispatchmethod

from open_investing.task_spec.task_spec import TaskSpec, TaskSpecHandler


class TaskSpecHandlerRegistry:
    task_spec_handler_classes: Dict[str, Type[TaskSpecHandler]] = {}
    task_spec_classes: Dict[str, Type[TaskSpec]] = {}

    @classmethod
    def register_class(cls, target_cls: Type[TaskSpecHandler]):
        spec_type_name = target_cls.task_spec_cls.spec_type_name_classvar

        if spec_type_name in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {spec_type_name} is already registered")

        cls.task_spec_classes[spec_type_name] = target_cls.task_spec_cls
        cls.task_spec_handler_classes[spec_type_name] = target_cls

    # @classmethod
    # def (cls, target_cls: Type[TaskSpecHandler]):

    @singledispatchmethod
    @classmethod
    def create_handler_instance(cls, task_spec):
        raise NotImplementedError

    @create_handler_instance.register(TaskSpec)
    @classmethod
    def _(cls, task_spec: TaskSpec):
        task_spec_cls = type(task_spec)
        spec_type_name = task_spec_cls.spec_type_name_classvar

        if spec_type_name not in cls.task_spec_handler_classes:
            raise Exception(f"TaskSpec {spec_type_name} is not registered")

        task_spec_handler_cls = cls.task_spec_handler_classes[spec_type_name]

        return task_spec_handler_cls(task_spec)

    @create_handler_instance.register(dict)
    @classmethod
    def _(cls, task_spec: Dict):
        task_spec_ = cls.create_spec_instance(task_spec)

        return cls.create_handler_instance(task_spec_)

    @classmethod
    def create_spec_instance(cls, task_spec_dict: Dict) -> TaskSpec:
        spec_type_name = task_spec_dict["spec_type_name"]

        if spec_type_name not in cls.task_spec_classes:
            raise Exception(f"TaskSpec {spec_type_name} is not registered")

        task_spec_cls = cls.task_spec_classes[spec_type_name]
        task_spec = task_spec_cls(**task_spec_dict)

        return task_spec
