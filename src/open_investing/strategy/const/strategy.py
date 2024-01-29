#!/usr/bin/env python3

from enum import Enum


class StrategyLifeStage(str, Enum):
    Unstarted = "unstarted"

    Started = "started"
    Opened = "opened"

    Closed = "closed"


class StrategyCommandName(str, Enum):
    UserConfirm = "user_confirm"
