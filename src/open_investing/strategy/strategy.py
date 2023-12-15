#!/usr/bin/env python3

from abc import ABC, abstractmethod


class IStrategy(ABC):

    def __init__(self) -> None:

        self.decision: Decision = None
        pass
