from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class StrategyConfig:
    strategy: str = "microprice_as"
    gamma: float = 0.01
    kappa: float = 1.5
    horizon_seconds: float = 3600.0
    q_max: float = 50_000.0
    order_size: float = 1_000.0
    vol_window: int = 50
    update_on_each_book_event: bool = True
    snapshot_every_n_books: int = 1000
    max_events: int = 0


@dataclass
class DataConfig:
    lob_csv: str = "../MD/lob.csv"
    trades_csv: str = "../MD/trades.csv"


@dataclass
class OutputConfig:
    output_dir: str = "reports"
    report_md: str = "performance_report.md"
    metrics_csv: str = "metrics_timeseries.csv"
    fills_csv: str = "fills.csv"
    pnl_plot_png: str = "pnl_inventory.png"
    inventory_plot_png: str = "inventory_over_time.png"


@dataclass
class AppConfig:
    strategy: StrategyConfig
    data: DataConfig
    output: OutputConfig


def _from_dict(cls: Any, data: dict[str, Any]) -> Any:
    return cls(**{field: data.get(field) for field in cls.__dataclass_fields__})


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return AppConfig(
        strategy=_from_dict(StrategyConfig, raw.get("strategy", {})),
        data=_from_dict(DataConfig, raw.get("data", {})),
        output=_from_dict(OutputConfig, raw.get("output", {})),
    )
