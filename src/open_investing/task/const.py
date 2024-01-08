#!/usr/bin/env python3

from enum import Enum


class TaskCommandName(str, Enum):
    Start = "start"
    Stop = "stop"
    Command = "command"
