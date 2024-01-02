#!/usr/bin/env python3

from enum import Enum, auto


class DecisionLifeStage(str, Enum):
    Undefined = "undefined"
    Decided = "decided"

    Started = "started"
    Opened = "opened"

    Closed = "closed"
