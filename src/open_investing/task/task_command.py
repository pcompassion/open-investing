#!/usr/bin/env python3

from typing import Union, Dict
from pydantic import BaseModel
from open_investing.task_spec.task_spec import TaskSpec


class SubCommand(BaseModel):
    name: str


class TaskCommand(BaseModel):
    name: str
    sub_command: SubCommand | None = None
