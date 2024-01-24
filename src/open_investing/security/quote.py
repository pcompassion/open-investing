from pydantic import BaseModel
import datetime

from open_investing.price.money import Money


class Quote(BaseModel):
    ask_price_1: Money
    ask_volume_1: int

    bid_price_1: Money
    bid_volume_1: int

    ask_price_2: Money
    ask_volume_2: int

    bid_price_2: Money
    bid_volume_2: int

    ask_price_3: Money
    ask_volume_3: int

    bid_price_3: Money
    bid_volume_3: int

    ask_price_4: Money
    ask_volume_4: int

    bid_price_4: Money
    bid_volume_4: int

    ask_price_5: Money
    ask_volume_5: int

    bid_price_5: Money
    bid_volume_5: int

    date_at: datetime.datetime
