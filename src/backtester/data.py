from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd

from backtester.models import BookEvent, TradeEvent


def _resolve_data_path(base_dir: Path, input_path: str) -> Path:
    candidate = Path(input_path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def load_market_data(project_root: Path, lob_csv: str, trades_csv: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    lob_path = _resolve_data_path(project_root, lob_csv)
    trades_path = _resolve_data_path(project_root, trades_csv)

    lob = pd.read_csv(
        lob_path,
        usecols=["local_timestamp", "bids[0].price", "asks[0].price", "bids[0].amount", "asks[0].amount"],
    )
    trades = pd.read_csv(trades_path, usecols=["local_timestamp", "side", "price", "amount"])

    lob = lob.rename(columns={"local_timestamp": "timestamp"})
    trades = trades.rename(columns={"local_timestamp": "timestamp"})
    lob["timestamp"] = pd.to_numeric(lob["timestamp"], errors="coerce").astype("Int64")
    trades["timestamp"] = pd.to_numeric(trades["timestamp"], errors="coerce").astype("Int64")
    lob = lob.dropna(subset=["timestamp"]).copy()
    trades = trades.dropna(subset=["timestamp"]).copy()

    lob = lob.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    trades = trades.sort_values("timestamp", kind="mergesort").reset_index(drop=True)
    return lob, trades


def iter_merged_events(lob_df: pd.DataFrame, trades_df: pd.DataFrame) -> Iterator[BookEvent | TradeEvent]:
    lob_ts = lob_df["timestamp"].to_numpy()
    lob_bid = lob_df["bids[0].price"].to_numpy()
    lob_ask = lob_df["asks[0].price"].to_numpy()
    lob_bid_vol = lob_df["bids[0].amount"].to_numpy()
    lob_ask_vol = lob_df["asks[0].amount"].to_numpy()

    tr_ts = trades_df["timestamp"].to_numpy()
    tr_side = trades_df["side"].astype(str).str.lower().to_numpy()
    tr_price = trades_df["price"].to_numpy()
    tr_amount = trades_df["amount"].to_numpy()

    i = 0
    j = 0
    n_lob = len(lob_df)
    n_tr = len(trades_df)

    while i < n_lob or j < n_tr:
        take_lob = j >= n_tr or (i < n_lob and int(lob_ts[i]) <= int(tr_ts[j]))
        if take_lob:
            yield BookEvent(
                timestamp=int(lob_ts[i]),
                best_bid=float(lob_bid[i]),
                best_ask=float(lob_ask[i]),
                bid_volume=float(lob_bid_vol[i]),
                ask_volume=float(lob_ask_vol[i]),
            )
            i += 1
        else:
            side = tr_side[j]
            if side in {"buy", "sell"}:
                yield TradeEvent(
                    timestamp=int(tr_ts[j]),
                    side=side,
                    price=float(tr_price[j]),
                    amount=float(tr_amount[j]),
                )
            j += 1
