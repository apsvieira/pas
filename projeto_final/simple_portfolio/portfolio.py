"""Implementation of a simple portfolio."""
from typing import Optional

import pandas as pd

from order import OrderStore
from transaction import TransactionStore
from position import PositionStore


class Portfolio:
    def __init__(
        self,
        initial_capital: float,
        allocated_capital: Optional[float] = 0,
        positions: Optional[PositionStore] = None,
        transaction_history: Optional[TransactionStore] = None,
        orders: Optional[OrderStore] = None
    ) -> None:
        self.available_capital = initial_capital
        self.allocated_capital = allocated_capital
        self.positions = positions if positions is not None else PositionStore()
        self.transaction_history = transaction_history if transaction_history is not None else TransactionStore()
        self.orders = orders if orders is not None else OrderStore()

    def process_ticks(self, ticks: pd.DataFrame) -> None:
        # TODO perform tick checking?

        # TODO Implement logic to roll back a transaction and cancel related order if necessary.
        transactions_performed = self.orders.evaluate_open_orders(ticks)
        for order_id, transaction in transactions_performed:
            transaction_id = self.transaction_history.register_transaction(transaction)
            # TODO Log transaction performed
            profit_from_transaction, opened_contracts = self.positions.update_positions(transaction)

            self.available_capital += profit_from_transaction

            # TODO Replace 125 with asset.initial_margin when asset class is implemented
            margin_required = opened_contracts * 125
            # TODO Implement margin allocation function to check if it's possible to allocate the margin
            self.allocated_capital += margin_required
