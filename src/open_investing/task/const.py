#!/usr/bin/env python3

from enum import Enum


class ListenerType(Enum):
    Callable = "callable"
    ChannelGroup = "channel_group"
