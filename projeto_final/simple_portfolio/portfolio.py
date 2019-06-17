"""Implementation of a simple portfolio."""
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple

import numpy as np
import pandas as pd

from order import Order
from transaction import Transaction
from position import PositionStore
from utils import generate_id


class Portfolio:
    def __init__(
        self,
        initial_capital: float,
        allocated_capital: Optional[float] = 0,
        positions: Optional[PositionStore] = None,
        transaction_history: Optional[Dict] = None,
        open_orders: Optional[Dict] = None
    ) -> None:
        self.available_capital = initial_capital
        self.allocated_capital = allocated_capital
        self.positions = positions if positions is not None else PositionStore()
        self.transaction_history = transaction_history if transaction_history is not None else {}
        self.open_orders = open_orders if open_orders is not None else {}
        self.order_history = {}

    def process_ticks(self, ticks: pd.DataFrame) -> None:
        # TODO perform tick checking?

        total_profit = 0
        transactions_performed = self.evaluate_open_orders(ticks)
        for transaction in transactions_performed:
            transaction_id = self._register_transaction(transaction)
            profit_from_transaction, opened_contracts = self._update_positions(transaction)

            self.available_capital += profit_from_transaction

            # TODO Replace 125 with asset.initial_margin when asset class is implemented
            margin_required = opened_contracts * 125
            # TODO Implement margin allocation function to check if it's possible to allocated the margin
            self.allocated_capital += margin_required


    def _place_order(self, asset: 'str', price: float, quantity: int, order_type: str) -> None:
        existing_ids = list(self.open_orders.keys()) + list(self.order_history.keys())

        order_id = generate_id(existing_ids)
        order = Order(asset, price, quantity, order_type)
        order_pair = {order_id: order}

        open_orders = self.open_orders.copy()
        open_orders.update(order_pair)
        self.open_orders = open_orders

    def evaluate_open_orders(self, ticks: pd.DataFrame) -> List[Transaction]:
        """
        Evaluate the execution of the existing open orders after the closing of a tick.

        There are a couple of oversimplifications present in this function. See `_evaluate_order`.

        Parameters
        ----------
        ticks: pd.DataFrame, Tick data for each asset traded, including "high", "low" and "quantity".

        """
        open_orders = self.open_orders
        assets = np.unique([order.asset for order in open_orders.values()])
        timestamp = ticks.index.iloc[0]
        transactions_performed = []

        for asset in assets:
            asset_tick = ticks[asset]
            high = asset_tick['high']
            low = asset_tick['low']
            quantity = asset_tick['quantity']

            asset_orders = [order_id for order_id, order in open_orders.items() if order.asset == asset]
            for order_id in asset_orders:
                updated_order, transaction = self._evaluate_order(order_id, high, low, quantity, timestamp)

                if transaction is None:
                    continue
                transactions_performed.append(transaction)

        return transactions_performed

    # TODO This should be a function of the Order class
    def _evaluate_order(
        self,
        order_id: str,
        high: float,
        low: float,
        quantity: int,
        timestamp: Union[str, datetime]
    ) -> Tuple[Order, Optional[Transaction]]:
        """
        Evaluate the execution of a single order, given the tick prices.

        This function oversimplifies some aspects of the trading itself:
            1. An order is only held for 1 time frame. When a tick closes, all orders are evaluated
            and can be either executed or cancelled.
            2. An assumption is made that if the order is within the price range of the tick, the
            maximum possible quantity is traded. This ignores the queueing effects existent in
            exchange order books, and can lead to significant effects.
        """
        order = self.open_orders[order_id]
        price = order.price

        # If order price falls out of range, the order is cancelled.
        if price >= low and price <= high:
            updated_order = self._change_order_status(order_id, 'CANCELLED', order.quantity)
            transaction = None
        # If the order price is within the tick's low and high values, execute as much of the order as possible.
        else:
            traded_quantity = min(order.quantity, quantity)
            transaction = Transaction(order.asset, price, traded_quantity, order.order_type, timestamp)

            if traded_quantity > 0 and traded_quantity < order.quantity:
                updated_order = self._change_order_status(order_id, 'PARTIALLY_EXECUTED', traded_quantity)
            elif traded_quantity == order.quantity:
                updated_order = self._change_order_status(order_id, 'EXECUTED', traded_quantity)

        return updated_order, transaction

    def _register_transaction(self, transaction) -> str:
        transaction_id = generate_id(self.transaction_history.keys())

        transaction_history = self.transaction_history
        transaction_history.update({transaction_id: transaction})
        self.transaction_history = transaction_history

        return transaction_id

    # TODO This should be a function of the Order class
    def _change_order_status(self, order_id: str, status: str, quantity: int) -> Order:
        open_orders = self.open_orders
        order_history = self.order_history

        order = open_orders.pop(order_id)
        order.status = status
        order.quantity = quantity

        order_history.update({order_id: order})

        self.open_orders = open_orders
        self.order_history = order_history

        return order

    def _update_positions(self, transaction: Transaction) -> float:
        asset = transaction.asset
        positions = self.positions

        current_position = positions[asset]
        profit_realized = current_position.update(transaction)

        # TODO Include calculation of number of contracts opened in Position.update
        return profit_realized, 1
