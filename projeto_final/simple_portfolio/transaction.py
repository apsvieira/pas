from datetime import datetime
from typing import Union

import pandas as pd

from utils import generate_id


class Transaction:
    def __init__(
        self,
        asset: str,
        price: float,
        quantity: int,
        type: str,
        timestamp: Union[str, datetime]
    ) -> None:
        self.asset = asset
        self.price = price
        self.quantity = quantity
        self.type = type

        timestamp = timestamp if isinstance(timestamp, datetime) else pd._tslib.parse_datetime_string(timestamp)
        self.timestamp = timestamp

class TransactionStore(dict):
    def __init__(self, *args, **kwargs):
        super.__init__(*args, **kwargs)

    def register_transaction(self, transaction: Transaction) -> str:
        transaction_id = generate_id(self.keys())
        self[transaction_id] = transaction

        return transaction_id