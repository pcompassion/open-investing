#!/usr/bin/env python3

from pydantic import BaseModel
from typing import Dict, Union, Optional
from enum import Enum
from croniter import croniter
from datetime import datetime, timedelta

from open_library.extension.croniter_ex import estimate_interval, estimate_timeframe


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


    def estimated_timeframe(self, base_time=None):
        if self.cron_time:
            return estimate_timeframe(self.cron_time, base_time=base_time)

        return 0
