#!/usr/bin/env python3

from pydantic import BaseModel
from typing import Dict, Union, Optional
from enum import Enum
from croniter import croniter
from datetime import datetime, timedelta


# Base TaskSpec class
class TaskSpec(BaseModel):
    # Common fields for all TaskSpec

    cron_time: str
    data: Dict[str, Union[str, int, float]] = {}

    @property
    def spec_type_name(self):
        raise NotImplementedError("Subclasses should implement a type property")

    def estimated_interval(self, time_unit: TimeUnit = TimeUnit.SECOND):
        if self.cron_time:
            return estimate_interval(self.cron_time, time_unit=time_unit)

        return 0
