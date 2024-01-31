#!/usr/bin/env python3
from enum import Enum, auto
from itertools import chain


class IndexCode(str, Enum):
    Kospi = "kospi"
    Kospi200 = "kospi200"
    Krx100 = "krx100"
    Kosdaq = "kosdaq"
    Vkospi = "vkospi"


class BaseType(str, Enum):
    Stock = "Stock"


class DerivativeType(str, Enum):
    MiniFuture = "MiniFuture"
    MiniOption = "MiniOption"
    WeeklyOption = "WeeklyOption"
    Kosdaq150Future = "Kosdaq150Future"

    Future = "Future"
    Call = "Call"
    Put = "Put"
    Option = "Option"


# class SecurityType(str, Enum):
#     # https://stackoverflow.com/a/46080827
#     cls = vars()

#     for member in chain(list(BaseType), list(DerivativeType)):
#         cls[member.name] = member.value
#     del member, cls


class FieldName(str, Enum):
    SECURITY_CODE = "security_code"
    INDEX_CODE = "index_code"

    DERIVATIVE_NAME = "derivative_name"
