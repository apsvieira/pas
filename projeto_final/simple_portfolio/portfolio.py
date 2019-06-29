"""Implementation of a simple portfolio."""
import logging
from typing import List, Optional

import pandas as pd

from .order import Order, OrderStore
from .transaction import TransactionStore
from .position import PositionStore


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
        transactions_performed = self.orders.evaluate_open_orders(ticks)

        for order_id, transaction in transactions_performed:
            position, profit, opened_contracts = self.positions.update_position(transaction)

            # TODO Replace 125 with asset.initial_margin when asset class is implemented
            margin_required = opened_contracts * 125

            if self.available_capital - margin_required < 0:
                self.orders.rollback(order_id)
                continue

            trx_id, trx = self.transaction_history.register_transaction(transaction)
            self.logger.debug("Transaction {} Registered: {} {} {} contracts at {:.2f}.".format(
                trx_id, trx.type, trx.quantity, trx.asset, trx.price
            ))

            self.positions[trx.asset] = position

            self.allocated_capital += margin_required
            self.available_capital += profit - margin_required

        orders_to_issue = self.evaluate_signals(ticks, signals)
        for asset, price, quantity, order_type in orders_to_issue:
            order_id = self.orders.place_order(asset, price, quantity, order_type)

    def evaluate_signals(self, ticks: pd.DataFrame, signals: pd.DataFrame) -> List[Order]:
        non_null = signals.query('signal != 0').reset_index()
        num_signals = non_null.shape[0]

        orders_to_issue = []
        for idx in range(num_signals):
            asset_signal = non_null.iloc[idx]
            asset = asset_signal['asset']

            direction = 'SHORT' if asset_signal['signal'] == -1 else 'LONG'
            order_size = self._get_order_size(asset, direction)
            price = self._get_order_price(ticks.xs(asset, level='asset'), direction)

            order_params = [asset, price, order_size, direction]
            orders_to_issue.append(order_params)

        return orders_to_issue

    def _get_order_size(self, asset: str, direction: str) -> int:
        # TODO Implement logic to decide order size based on current positions.
        return 100

    def _get_order_price(self, tick, direction: str) -> float:
        # TODO Implement logic to decide order price based on current positions.
        price = tick['low'].values[0] if direction == 'SHORT' else tick['high'].values[0]
        return price

    def backtest(self, ticks: pd.DataFrame, signals: pd.DataFrame) -> float:
        tick_times = ticks.index.get_level_values('datetime').unique()
        for i, time in enumerate(tick_times):
            period_ticks = ticks.loc[time:time]
            period_signals = signals.loc[time:time]
            self.logger.info(f"Period {i}: Evaluating information for {time}.")
            self.process_ticks(period_ticks, period_signals)

        return self.available_capital

    def __repr__(self):
        positions_summary = self.positions.summary()
        message = f"""
        Portfolio:
            ----
        Available Capital: {self.available_capital}
        Allocated Capital: {self.allocated_capital}

        Current Positions: {positions_summary}
        """

        return message
