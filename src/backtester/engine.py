from __future__ import annotations

from pathlib import Path

from backtester.config import AppConfig
from backtester.data import iter_merged_events, load_market_data
from backtester.metrics import MetricsTracker
from backtester.models import BookEvent, Fill, TradeEvent
from backtester.order_manager import OrderManager
from backtester.strategy import build_strategy


class BacktestEngine:
    def __init__(self, config: AppConfig, project_root: Path) -> None:
        self.config = config
        self.project_root = project_root
        self.strategy = build_strategy(config.strategy)
        self.orders = OrderManager()
        self.metrics = MetricsTracker()
        self.last_mid = 0.0
        self.last_timestamp = 0
        self._book_counter = 0
        self._event_counter = 0

    def run(self) -> MetricsTracker:
        lob_df, trades_df = load_market_data(
            self.project_root, self.config.data.lob_csv, self.config.data.trades_csv
        )
        for event in iter_merged_events(lob_df, trades_df):
            self._event_counter += 1
            if self.config.strategy.max_events > 0 and self._event_counter > self.config.strategy.max_events:
                break
            self.last_timestamp = event.timestamp
            if isinstance(event, BookEvent):
                self._on_book(event)
            elif isinstance(event, TradeEvent):
                self._on_trade(event)
        if self.last_mid > 0:
            self.metrics.snapshot(self.last_timestamp, self.last_mid)
        return self.metrics

    def _on_book(self, event: BookEvent) -> None:
        self.last_mid = event.mid
        bid_price, ask_price = self.strategy.quote(event, self.metrics.inventory)
        self.orders.cancel_all()
        self.orders.place_two_sided(event.timestamp, bid_price, ask_price, self.config.strategy.order_size)
        self._book_counter += 1
        stride = max(int(self.config.strategy.snapshot_every_n_books), 1)
        if self._book_counter % stride == 0:
            self.metrics.snapshot(event.timestamp, self.last_mid)

    def _on_trade(self, event: TradeEvent) -> None:
        bid_order = self.orders.active.bid
        ask_order = self.orders.active.ask

        if bid_order and event.side == "sell" and event.price <= bid_order.price:
            fill_amount = min(event.amount, bid_order.remaining)
            if fill_amount > 0:
                bid_order.remaining -= fill_amount
                self.metrics.on_fill(
                    Fill(
                        timestamp=event.timestamp,
                        side="buy",
                        price=bid_order.price,
                        amount=fill_amount,
                        mid_reference=self.last_mid,
                    )
                )
            if bid_order.remaining <= 0:
                self.orders.active.bid = None

        if ask_order and event.side == "buy" and event.price >= ask_order.price:
            fill_amount = min(event.amount, ask_order.remaining)
            if fill_amount > 0:
                ask_order.remaining -= fill_amount
                self.metrics.on_fill(
                    Fill(
                        timestamp=event.timestamp,
                        side="sell",
                        price=ask_order.price,
                        amount=fill_amount,
                        mid_reference=self.last_mid,
                    )
                )
            if ask_order.remaining <= 0:
                self.orders.active.ask = None
