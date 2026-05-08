from __future__ import annotations

from backtester.models import ActiveOrders, Order


class OrderManager:
    """Stores at most one active bid and one active ask."""

    def __init__(self) -> None:
        self.active = ActiveOrders()

    def cancel_all(self) -> None:
        self.active.bid = None
        self.active.ask = None

    def place_two_sided(self, timestamp: int, bid_price: float, ask_price: float, size: float) -> None:
        self.active.bid = Order(side="buy", price=bid_price, remaining=size, created_ts=timestamp)
        self.active.ask = Order(side="sell", price=ask_price, remaining=size, created_ts=timestamp)
