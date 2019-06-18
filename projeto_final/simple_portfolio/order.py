from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# from asset import Asset
from transaction import Transaction
from utils import generate_id

TYPES = (
    'LONG',
    'SHORT',
    'ZERO',
)


class Order:
    def __init__(self, asset: str, price: float, quantity: int, order_type: str, status: str = 'OPEN') -> None:
        assert price > 0, f"Placed order with zero or negative price ({price})."
        assert quantity > 0, f"Placed order for zero or negative quantity of contracts ({quantity})."
        assert order_type in TYPES, f"Placed order with invalid type {order_type}. Should be one of {TYPES}."

        self.asset = asset
        self.price = price
        self.quantity = quantity
        self.order_type = order_type

    def evaluate_execution(
        self,
        high: float,
        low: float,
        quantity: int,
        timestamp: Union[str, datetime]
    ) -> Tuple['Order', Optional[Transaction]]:
        """
        Evaluate the execution of a single order, given the tick prices.

        This function oversimplifies some aspects of the trading itself:
            1. An order is only held for 1 time frame. When a tick closes, all orders are evaluated
            and can be either executed or cancelled.
            2. An assumption is made that if the order is within the price range of the tick, the
            maximum possible quantity is traded. This ignores the queueing effects existent in
            exchange order books, and can lead to significant effects.
        """
        price = self.price

        # If order price falls out of range, the order is cancelled.
        if price < low or price > high:
            # TODO Age order here. If order has hit maximum aging, cancel.
            updated_order = Order(self.asset, self.price, self.quantity, self.order_type, 'CANCELLED')
            transaction = None
        # If the order price is within the tick's low and high values, execute as much of the order as possible.
        else:
            traded_quantity = min(self.quantity, quantity)
            transaction = Transaction(self.asset, price, traded_quantity, self.order_type, timestamp)

            if traded_quantity > 0 and traded_quantity < self.quantity:
                updated_order = Order(self.asset, price, traded_quantity, self.order_type, 'PARTIALLY_EXECUTED')
            elif traded_quantity == self.quantity:
                updated_order = Order(self.asset, price, traded_quantity, self.order_type, 'EXECUTED')

        return updated_order, transaction


class OrderStore(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def evaluate_open_orders(self, ticks: pd.DataFrame) -> List[Transaction]:
        """
        Evaluate the execution of the existing open orders after the closing of a tick.

        There are a couple of oversimplifications present in this function. See `evaluate_execution`.

        Parameters
        ----------
        ticks: pd.DataFrame, Tick data for each asset traded, including "high", "low" and "quantity".

        """
        open_orders = self.get_open_orders()
        assets = np.unique([order.asset for order in open_orders.values()])
        timestamp = ticks.index.iloc[0]
        transactions_performed = []

        for asset in assets:
            asset_tick = ticks[asset]
            high = asset_tick['high']
            low = asset_tick['low']
            quantity = asset_tick['quantity']

            asset_orders = {order_id: order for order_id, order in open_orders.items() if order.asset == asset}
            for order_id, order in asset_orders.items():
                updated_order, transaction = order.evaluate_execution(high, low, quantity, timestamp)
                self[order_id] = updated_order

                if transaction is None:
                    continue
                transactions_performed.append((order_id, transaction))

        return transactions_performed

    def get_open_orders(self) -> Dict[str, Order]:
        open_orders = {order_id: order for order_id, order in self.items() if order.status == 'OPEN'}
        return open_orders

    def place_order(self, asset: 'str', price: float, quantity: int, order_type: str) -> str:
        existing_ids = list(self.keys())

        order_id = generate_id(existing_ids)
        order = Order(asset, price, quantity, order_type)
        self[order_id] = order

        return order_id

    def rollback(self, order_id: str) -> str:
        order = self[order_id]
        # TODO If there is aging, status must go OPEN -> age -> CANCELLED
        order.status = 'CANCELLED'
        self[order_id] = order

        return order_id
