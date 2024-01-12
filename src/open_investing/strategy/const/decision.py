#!/usr/bin/env python3

from enum import Enum, auto


class DecisionLifeStage(str, Enum):
    Undefined = "undefined"
    Decided = "decided"

    Started = "started"
    Opened = "opened"
    Fullfilled = "fullfilled"

    Closing = "closing"
    Closed = "closed"

    @property
    def is_active(self):
        return self in [self.Decided, self.Started, self.Opened]

    @property
    def started_closing(self):
        return self in [self.Closing, self.Closed]


class DecisionCommandName(str, Enum):
    Open = "open"
    Cancel = "cancel"
    CancelRemaining = "cancel_remaining"
    Close = "close"

    Start = "start"

    Echo = "echo"
