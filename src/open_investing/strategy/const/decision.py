#!/usr/bin/env python3

from enum import Enum, auto


class DecisionLifeStage(str, Enum):
    UNOPENED = "unopened"
    OPENED = "opened"
    STARTED = "started"
    CLOSED = "closed"
