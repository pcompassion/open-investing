#!/usr/bin/env python3


class StrategyFactory:
    class_map = {}

    @classmethod
    def register_class(cls, class_name, class_ref):
        cls.class_map[class_name.lower()] = class_ref

    @classmethod
    def create_instance(cls, class_name):
        class_ref = cls.class_map.get(class_name.lower())
        if class_ref is not None:
            return class_ref()
        else:
            raise ValueError(f"No class registered for '{class_name}'")
