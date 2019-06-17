# from asset import Asset


TYPES = (
    'LONG',
    'SHORT',
    'ZERO',
)


class Order:
    def __init__(self, asset: str, price: float, quantity: int, order_type: str, status: str = 'OPEN'):
        assert price > 0, f"Placed order with zero or negative price ({price})."
        assert quantity > 0, f"Placed order for zero or negative quantity of contracts ({quantity})."
        assert order_type in TYPES, f"Placed order with invalid type {order_type}. Should be one of {TYPES}."

        self.asset = asset
        self.price = price
        self.quantity = quantity
        self.order_type = order_type
