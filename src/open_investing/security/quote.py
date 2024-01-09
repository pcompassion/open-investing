from pydantic import BaseModel
import datetime


class Quote(BaseModel):
    ask_price_1: float
    ask_volume_1: int

    bid_price_1: float
    bid_volume_1: int

    ask_price_2: float
    ask_volume_2: int

    bid_price_2: float
    bid_volume_2: int

    ask_price_3: float
    ask_volume_3: int

    bid_price_3: float
    bid_volume_3: int

    ask_price_4: float
    ask_volume_4: int

    bid_price_4: float
    bid_volume_4: int

    ask_price_5: float
    ask_volume_5: int

    bid_price_5: float
    bid_volume_5: int

    date_at: datetime.datetime
