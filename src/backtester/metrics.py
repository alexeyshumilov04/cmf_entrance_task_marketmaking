from __future__ import annotations

from dataclasses import dataclass, field
import math

import pandas as pd

from backtester.models import Fill


@dataclass
class MetricsTracker:
    cash: float = 0.0
    inventory: float = 0.0
    turnover: float = 0.0
    realized_pnl: float = 0.0
    fills: list[Fill] = field(default_factory=list)
    timeseries: list[dict] = field(default_factory=list)

    def on_fill(self, fill: Fill) -> None:
        self.fills.append(fill)
        notional = fill.price * fill.amount
        self.turnover += notional
        if fill.side == "buy":
            self.cash -= notional
            self.inventory += fill.amount
        else:
            self.cash += notional
            self.inventory -= fill.amount

    def snapshot(self, timestamp: int, mid: float) -> None:
        mtm_pnl = self.cash + self.inventory * mid
        self.realized_pnl = self.cash
        self.timeseries.append(
            {
                "timestamp": timestamp,
                "mid": mid,
                "cash": self.cash,
                "inventory": self.inventory,
                "turnover": self.turnover,
                "realized_pnl": self.realized_pnl,
                "mtm_pnl": mtm_pnl,
            }
        )

    def timeseries_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.timeseries)

    def fills_df(self) -> pd.DataFrame:
        return pd.DataFrame([fill.__dict__ for fill in self.fills])

    def summary_metrics(self) -> dict[str, float]:
        ts = self.timeseries_df()
        fills = self.fills_df()
        if ts.empty:
            return {
                "final_pnl": 0.0,
                "final_inventory": 0.0,
                "turnover": 0.0,
                "sharpe_annualized": 0.0,
                "max_drawdown": 0.0,
                "max_drawdown_duration_sec": 0.0,
                "hit_rate": 0.0,
                "total_duration_seconds": 0.0,
            }

        final_pnl = float(ts["mtm_pnl"].iloc[-1])
        final_inventory = float(ts["inventory"].iloc[-1])
        turnover = float(ts["turnover"].iloc[-1])
        duration_sec = _duration_seconds(ts)
        sharpe = _annualized_sharpe(ts, duration_sec)
        max_dd, max_dd_dur = _max_drawdown_with_duration(ts)
        hit_rate = _hit_rate(fills)
        return {
            "final_pnl": final_pnl,
            "final_inventory": final_inventory,
            "turnover": turnover,
            "sharpe_annualized": sharpe,
            "max_drawdown": max_dd,
            "max_drawdown_duration_sec": max_dd_dur,
            "hit_rate": hit_rate,
            "total_duration_seconds": duration_sec,
        }


def _duration_seconds(ts: pd.DataFrame) -> float:
    valid = ts[ts["timestamp"] >= 0]
    if len(valid) < 2:
        return 0.0
    return float((valid["timestamp"].iloc[-1] - valid["timestamp"].iloc[0]) / 1e9)


def _annualized_sharpe(ts: pd.DataFrame, total_duration_seconds: float) -> float:
    if len(ts) < 2 or total_duration_seconds <= 0:
        return 0.0
    pnl_diff = ts["mtm_pnl"].diff().dropna()
    if pnl_diff.empty:
        return 0.0
    std = float(pnl_diff.std(ddof=0))
    if std == 0:
        return 0.0
    mean = float(pnl_diff.mean())
    scale = math.sqrt(252 * 6.5 * 3600 / total_duration_seconds)
    return (mean / std) * scale


def _max_drawdown_with_duration(ts: pd.DataFrame) -> tuple[float, float]:
    pnl = ts["mtm_pnl"]
    running_max = pnl.cummax()
    drawdown = running_max - pnl
    max_dd = float(drawdown.max()) if not drawdown.empty else 0.0
    if max_dd <= 0:
        return 0.0, 0.0

    peak_idx = drawdown.idxmax()
    peak_value = float(running_max.loc[peak_idx])
    peak_start_idx = int((pnl.loc[:peak_idx] == peak_value).idxmax())

    ts_start = float(ts.loc[peak_start_idx, "timestamp"])
    ts_end = float(ts.loc[peak_idx, "timestamp"])
    duration = max((ts_end - ts_start) / 1e9, 0.0)
    return max_dd, duration


def _hit_rate(fills: pd.DataFrame) -> float:
    if fills.empty:
        return 0.0
    signed = fills.apply(lambda r: r["price"] * r["amount"] if r["side"] == "sell" else -r["price"] * r["amount"], axis=1)
    non_zero = signed[signed != 0]
    if non_zero.empty:
        return 0.0
    profitable = int((non_zero > 0).sum())
    return profitable / len(non_zero)
