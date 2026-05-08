from __future__ import annotations

import math
from collections import deque

from backtester.config import StrategyConfig
from backtester.models import BookEvent


class BaseASStrategy:
    def __init__(self, cfg: StrategyConfig) -> None:
        self.cfg = cfg
        self._history: deque[float] = deque(maxlen=cfg.vol_window)
        self._t0: int | None = None

    def fair_price(self, event: BookEvent) -> float:
        raise NotImplementedError

    def _update_vol(self, reference_price: float) -> float:
        self._history.append(reference_price)
        if len(self._history) < 2:
            return 0.0
        returns = [math.log(self._history[i] / self._history[i - 1]) for i in range(1, len(self._history))]
        mean_r = sum(returns) / len(returns)
        var = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        return math.sqrt(var)

    def quote(self, event: BookEvent, inventory: float) -> tuple[float, float]:
        s = self.fair_price(event)
        if s <= 0:
            return event.best_bid, event.best_ask

        sigma = self._update_vol(s)
        if sigma <= 0:
            return event.best_bid, event.best_ask

        if self._t0 is None:
            self._t0 = event.timestamp
        elapsed = max((event.timestamp - self._t0) / 1e9, 0.0)
        t_remaining = max(self.cfg.horizon_seconds - elapsed, 1.0)

        q = max(-self.cfg.q_max, min(self.cfg.q_max, inventory))
        sigma_p = max(event.spread, min(sigma * s, s * 0.005))

        r = s - q * self.cfg.gamma * sigma_p * sigma_p * t_remaining
        delta = self.cfg.gamma * sigma_p * sigma_p * t_remaining + (2.0 / self.cfg.gamma) * math.log(
            1.0 + self.cfg.gamma / self.cfg.kappa
        )
        delta = max(event.spread, min(delta, s * 0.001))

        bid_price = r - delta / 2.0
        ask_price = r + delta / 2.0

        inv_ratio = q / max(self.cfg.q_max, 1e-9)
        if inv_ratio > 0.5:
            ask_price -= delta * 0.3 * inv_ratio
            bid_price -= delta * 0.5 * inv_ratio
        elif inv_ratio < -0.5:
            bid_price += delta * 0.3 * abs(inv_ratio)
            ask_price += delta * 0.5 * abs(inv_ratio)

        if bid_price >= event.best_ask:
            bid_price = event.best_ask - event.spread * 0.1
        if ask_price <= event.best_bid:
            ask_price = event.best_bid + event.spread * 0.1
        return bid_price, ask_price


class AvellanedaStoikov2008(BaseASStrategy):
    def fair_price(self, event: BookEvent) -> float:
        return event.mid


class MicropriceAS2018(BaseASStrategy):
    def fair_price(self, event: BookEvent) -> float:
        return event.microprice


def build_strategy(cfg: StrategyConfig) -> BaseASStrategy:
    key = cfg.strategy.lower()
    if key in {"as", "avellaneda_stoikov", "avellaneda-stoikov", "as2008"}:
        return AvellanedaStoikov2008(cfg)
    if key in {"microprice_as", "microprice-as", "mpas", "as2018"}:
        return MicropriceAS2018(cfg)
    raise ValueError(f"Unsupported strategy: {cfg.strategy}")
