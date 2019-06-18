from collections import defaultdict
from typing import Dict, Optional, Tuple

from transaction import Transaction


class Position:
    # By keeping short entries sorted in crescent order and long entries sorted in decrescent order,
    # we can pop the last entry of each to evaluate updating a position, and append if necessary.
    # This will be the short entry with the highest price or the long entry with the lowest price.
    _entry_sort_order = {
        'SHORT': False,
        'LONG': True
    }

    def __init__(
        self,
        asset: str,
        entries: Optional[Dict] = None
    ) -> None:
        self.asset = asset

        self.entries = {
            'SHORT': [],
            'LONG': []
        } if entries is None else entries

    @staticmethod
    def _make_entry(entry_price, quantity):
        entry = {
            'entry_price': entry_price,
            'quantity': quantity,
        }

        return entry

    def update(self, transaction: Transaction) -> Tuple['Position', float, int]:
        profit, liquidated_quantity = self._liquidate_opposite_entries(transaction)

        if liquidated_quantity < transaction.quantity:
            updated_entries = self._register_entry(transaction)
            self.entries = updated_entries

        return self, profit, liquidated_quantity

    def _register_entry(self, transaction: Transaction) -> Dict:
        direction = transaction.type
        new_entry = self._make_entry(transaction.price, transaction.quantity)

        current_entries = self.entries.copy()
        entry_list = current_entries[direction]
        entry_list.append(new_entry)

        entry_list = sorted(
            entry_list,
            key=lambda pos: pos['entry_price'],
            reverse=self._entry_sort_order[direction]
        )

        current_entries[direction] = entry_list
        return current_entries

    def _liquidate_opposite_entries(self, transaction: Transaction) -> Tuple[float, float]:
        current_entries = self.entries.copy()

        other_direction = 'SHORT' if transaction.type == 'LONG' else 'LONG'
        opposite_entries = current_entries[other_direction]

        if len(opposite_entries) == 0:
            return 0, 0

        # profit := (short_price - long_price) * traded_quantity
        profit_mult = -1 if other_direction == 'LONG' else 1

        total_liquidated_quantity = 0
        total_profit = 0

        while total_liquidated_quantity < transaction.quantity:
            entry = opposite_entries.pop()
            opposite_quantity = entry['quantity']

            liquidated_quantity = min(opposite_quantity, transaction.quantity)
            total_profit += profit_mult * (entry['entry_price'] - transaction.price) * liquidated_quantity

            if liquidated_quantity < opposite_quantity:
                opposite_quantity = opposite_quantity - liquidated_quantity
                entry['quantity'] = opposite_quantity
                opposite_entries.append(entry)

            total_liquidated_quantity += liquidated_quantity

        current_entries[other_direction] = opposite_entries
        self.entries = current_entries

        return total_profit, total_liquidated_quantity


class PositionStore(defaultdict):
    def __init__(self, positions: Optional[Dict] = None) -> None:
        positions = {} if positions is None else positions

        keys, values = [list(it) for it in (positions.keys(), positions.values())]
        assert all((isinstance(asset, str) for asset in keys)), f"All keys should be strings. Got {keys}."
        assert all((isinstance(pos, Position) for pos in values)),\
            f"All positions should be instances of 'Position'. Got {values}."

        super().__init__(Position, positions)

    def __missing__(self, key: str) -> Position:
        self[key] = new = self.default_factory(key)
        return new

    # TODO implement logic to roll back a transaction
    def update_position(self, transaction: Transaction) -> Tuple[float, int]:
        asset_position = self[transaction.asset]
        updated_position, profit_realized, liquidated_quantity = asset_position.update(transaction)
        self[transaction.asset] = updated_position

        # For each liquidated contract, there were one short and one long contracts closed.
        opened_contracts = transaction.quantity - 2 * liquidated_quantity

        return profit_realized, opened_contracts
