class Futures:
    def __init__(self, asset: str, enter_price: float, initial_margin: float = 15) -> None:
        self.asset = asset
        self.last_price = enter_price
        self.margin = initial_margin

    def _calculate_margin_change(self, price):
        past_price = self.last_price
        price_change = past_price - price