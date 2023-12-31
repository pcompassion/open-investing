#!/usr/bin/env python3
from enum import Enum, auto


class IndexCode(str, Enum):
    Kospi = "kospi"
    Kospi200 = "kospi200"
    Krx100 = "krx100"
    Kosdaq = "kosdaq"
    Vkospi = "vkospi"


class DerivativeType(str, Enum):
    MiniFuture = "MiniFuture"
    MiniOption = "MiniOption"
    WeeklyOption = "WeeklyOption"
    Kosdaq150Future = "Kosdaq150Future"

    Future = "Future"
    Call = "Call"
    Put = "Put"


class FieldName(str, Enum):
    SECURITY_CODE = "security_code"
    INDEX_CODE = "index_code"

    DERIVATIVE_NAME = "derivative_name"
