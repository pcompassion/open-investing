#!/usr/bin/env python3

from typing import Union, Dict
from pydantic import BaseModel
from open_investing.task_spec.task_spec import TaskSpec


class TaskCommand(BaseModel):
    command_name: str
    task_spec: TaskSpec
