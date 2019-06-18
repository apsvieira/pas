"""Implementation of a simple portfolio."""
import logging
from typing import List, Optional

import pandas as pd

from order import OrderStore
from transaction import TransactionStore
from position import PositionStore


LOG_FORMAT = "%(levelname)s %(asctime)s - %(name)s: %(message)s"

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

        logging.basicConfig(format=LOG_FORMAT)
        self.logger = logging.getLogger(name="MyPortfolio")

    def process_ticks(self, ticks: pd.DataFrame, signals: pd.DataFrame) -> None:
        # TODO perform tick checking?

        # TODO Implement logic to roll back a transaction and cancel related order if necessary.
        transactions_performed = self.orders.evaluate_open_orders(ticks)

        for order_id, transaction in transactions_performed:
            trx_id, trx = self.transaction_history.register_transaction(transaction)
            self.logger.debug("Transaction {} Registered: {} {} {} contracts at {:.2f}.".format(
                trx_id, trx.type, trx.quantity, trx.asset, trx.price
            ))

            profit_from_transaction, opened_contracts = self.positions.update_position(transaction)
            self.available_capital += profit_from_transaction

            # TODO Replace 125 with asset.initial_margin when asset class is implemented
            margin_required = opened_contracts * 125
            self.allocated_capital += margin_required
            self.available_capital -= margin_required

            # TODO Implement margin allocation function to check if it's possible to allocate the margin
            # For rollbacks to be "simple", everything needs to be "pure": if no functions or methods
            # change the underlying state of objects, but instead return new instances, we can decide
            # wether or not a transaction can take place and THEN change things. The rollback becomes a no-op.
            rollback = False
            if rollback:
                self.orders.rollback(order_id)
                self.transaction_history.rollback(order_id)

        orders_to_issue = self.evaluate_signals(signals)
        for asset, price, quantity, order_type in orders_to_issue:
            self.orders.place_order(asset, price, quantity, order_type)

    # TODO
    def evaluate_signals(self, signals: pd.DataFrame) -> List:
        return []