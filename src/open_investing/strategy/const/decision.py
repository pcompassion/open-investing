#!/usr/bin/env python3

from enum import Enum, auto


class DecisionLifeStage(str, Enum):
    Undefined = "undefined"
    Started = "started"
    Decided = "decided"

    ExchangeOpenRequest = "exchange.open_request"  # place request
    ExchangeOpenSuccess = "exchange.open_success"  # place success
    ExchangeOpenFailure = "exchange.open_failure"

    Opened = "opened"  # partial filled
    Fullfilled = "fullfilled"  # fully filled
    FullyOffsetted = "fully_offsetted"  # fully offsetted

    Closed = "closed"

    @property
    def is_active(self):
        return self in [
            self.Decided,
            self.ExchangeOpenRequest,
            self.ExchangeOpenSuccess,
            self.ExchangeOpenFailure,
            self.Opened,
            self.Fullfilled,
        ]

    @property
    def has_opened(self):
        return self not in [
            self.Undefined,
            self.Decided,
            self.ExchangeOpenRequest,
            self.ExchangeOpenSuccess,
            self.ExchangeOpenFailure,
        ]

    @property
    def started_closing(self):
        return self in [self.Closing, self.Closed]


class DecisionCommandName(str, Enum):
    Open = "open"
    Cancel = "cancel"
    CancelRemaining = "cancel_remaining"
    Close = "close"
    Offset = "offset"

    Start = "start"

    Echo = "echo"


class DecisionEventName(str, Enum):
    Fullfilled = "fullfilled"
    FullyOffsetted = "fully_offsetted"
