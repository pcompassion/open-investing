#!/usr/bin/env python3

from enum import Enum


class ListenerType(Enum):
    Callable = "callable"
    ChannelGroup = "channel_group"


class TaskCommandName(str, Enum):
    Start = "start"
    Stop = "stop"
    Command = "command"
