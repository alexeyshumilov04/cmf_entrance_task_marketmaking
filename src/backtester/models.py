from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BookEvent:
    timestamp: int
    best_bid: float
    best_ask: float
    bid_volume: float
    ask_volume: float

    @property
    def mid(self) -> float:
        return (self.best_bid + self.best_ask) / 2.0

    @property
    def spread(self) -> float:
        return max(self.best_ask - self.best_bid, 1e-12)

    @property
    def microprice(self) -> float:
        total = self.bid_volume + self.ask_volume
        if total <= 0:
            return self.mid
        return self.best_ask * (self.bid_volume / total) + self.best_bid * (self.ask_volume / total)


@dataclass
class TradeEvent:
    timestamp: int
    side: str
    price: float
    amount: float


@dataclass
class Order:
    side: str
    price: float
    remaining: float
    created_ts: int


@dataclass
class Fill:
    timestamp: int
    side: str
    price: float
    amount: float
    mid_reference: float


@dataclass
class ActiveOrders:
    bid: Optional[Order] = None
    ask: Optional[Order] = None
