#!/usr/bin/env python3


class StartupRegistry:
    startup_classes = []

    has_run = False

    @classmethod
    def register_startup_class(cls, target_cls):
        if cls.has_run:
            raise RuntimeError("StartupRegistry has already run.")
        cls.startup_classes.append(target_cls)
        return target_cls

    @classmethod
    def initialize_startup_classes(cls):
        for registered_cls in cls.startup_classes:
            obj = registered_cls()
            obj.init()
        cls.has_run = True
