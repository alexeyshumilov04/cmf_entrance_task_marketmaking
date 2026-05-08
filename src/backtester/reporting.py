from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from backtester.config import AppConfig
from backtester.metrics import MetricsTracker


def save_outputs(config: AppConfig, project_root: Path, metrics: MetricsTracker) -> dict[str, Path]:
    output_dir = (project_root / config.output.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = metrics.timeseries_df()
    fills = metrics.fills_df()

    metrics_csv = output_dir / config.output.metrics_csv
    fills_csv = output_dir / config.output.fills_csv
    report_md = output_dir / config.output.report_md
    png_path = output_dir / config.output.pnl_plot_png
    inventory_png = output_dir / config.output.inventory_plot_png

    if not ts.empty:
        ts.to_csv(metrics_csv, index=False)
    else:
        pd.DataFrame(columns=["timestamp", "mtm_pnl", "inventory"]).to_csv(metrics_csv, index=False)

    if not fills.empty:
        fills.to_csv(fills_csv, index=False)
    else:
        pd.DataFrame(columns=["timestamp", "side", "price", "amount"]).to_csv(fills_csv, index=False)

    _save_plot(ts, png_path)
    _save_inventory_plot(ts, inventory_png)
    _save_report(config, report_md, metrics.summary_metrics(), fills)

    return {
        "metrics_csv": metrics_csv,
        "fills_csv": fills_csv,
        "report_md": report_md,
        "plot_png": png_path,
        "inventory_png": inventory_png,
    }


def _save_plot(ts: pd.DataFrame, path: Path) -> None:
    plt.figure(figsize=(12, 6))
    if not ts.empty:
        x = range(len(ts))
        plt.plot(x, ts["mtm_pnl"], label="MtM PnL")
        plt.plot(x, ts["inventory"], label="Inventory")
    plt.title("PnL and Inventory Over Time")
    plt.xlabel("Event Index")
    plt.ylabel("Value")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()


def _save_inventory_plot(ts: pd.DataFrame, path: Path) -> None:
    plt.figure(figsize=(12, 5))
    if not ts.empty:
        plt.plot(ts["timestamp"], ts["inventory"], label="Inventory")
    plt.title("Inventory vs Time")
    plt.xlabel("Timestamp (ns)")
    plt.ylabel("Inventory")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()


def _save_report(config: AppConfig, report_path: Path, summary: dict[str, float], fills: pd.DataFrame) -> None:
    final_mtm = summary["final_pnl"]
    final_inventory = summary["final_inventory"]
    final_turnover = summary["turnover"]
    sharpe = summary["sharpe_annualized"]
    max_dd = summary["max_drawdown"]
    max_dd_duration = summary["max_drawdown_duration_sec"]
    hit_rate = summary["hit_rate"]
    total_duration = summary["total_duration_seconds"]

    buy_fills = int((fills["side"] == "buy").sum()) if not fills.empty else 0
    sell_fills = int((fills["side"] == "sell").sum()) if not fills.empty else 0

    report = f"""# Performance Report

## Strategy
- Name: `{config.strategy.strategy}`
- gamma: `{config.strategy.gamma}`
- kappa: `{config.strategy.kappa}`
- horizon_seconds: `{config.strategy.horizon_seconds}`
- q_max: `{config.strategy.q_max}`
- order_size: `{config.strategy.order_size}`
- vol_window: `{config.strategy.vol_window}`

## Core Metrics
- Final MtM PnL: `{final_mtm:.6f}`
- Final Inventory: `{final_inventory:.6f}`
- Turnover: `{final_turnover:.6f}`
- Sharpe Ratio (annualized, rf=0): `{sharpe:.6f}`
- Max Drawdown (absolute PnL): `{max_dd:.6f}`
- Max Drawdown Duration (sec): `{max_dd_duration:.6f}`
- Hit-rate: `{hit_rate:.6%}`
- Total Duration (sec): `{total_duration:.6f}`
- Number of Buy Fills: `{buy_fills}`
- Number of Sell Fills: `{sell_fills}`

## Notes
- Backtest processes merged `lob.csv` and `trades.csv` events by `local_timestamp`.
- Engine uses up to one active bid and one active ask order.
- Partial fill logic is enabled.
- No fees and no slippage are applied.
"""
    report_path.write_text(report, encoding="utf-8")


def save_comparison_report(
    report_path: Path,
    ts_as2008: pd.DataFrame,
    ts_microprice: pd.DataFrame,
    summary_as2008: dict[str, float],
    summary_microprice: dict[str, float],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    pnl_plot_path = report_path.parent / "comparison_pnl.png"
    inventory_plot_path = report_path.parent / "comparison_inventory.png"
    _save_comparison_plot(ts_as2008, ts_microprice, pnl_plot_path, "mtm_pnl", "PnL Comparison")
    _save_comparison_plot(ts_as2008, ts_microprice, inventory_plot_path, "inventory", "Inventory Comparison")

    rows = [
        ("Final PnL", summary_as2008["final_pnl"], summary_microprice["final_pnl"]),
        ("Sharpe (annualized)", summary_as2008["sharpe_annualized"], summary_microprice["sharpe_annualized"]),
        ("Max Drawdown", summary_as2008["max_drawdown"], summary_microprice["max_drawdown"]),
        (
            "Max Drawdown Duration (sec)",
            summary_as2008["max_drawdown_duration_sec"],
            summary_microprice["max_drawdown_duration_sec"],
        ),
        ("Hit-rate", summary_as2008["hit_rate"], summary_microprice["hit_rate"]),
        ("Turnover", summary_as2008["turnover"], summary_microprice["turnover"]),
        ("Final Inventory", summary_as2008["final_inventory"], summary_microprice["final_inventory"]),
    ]
    lines = [
        "# Strategy Comparison Report",
        "",
        "| Metric | AS2008 | MicropriceAS |",
        "|---|---:|---:|",
    ]
    for name, left, right in rows:
        if name == "Hit-rate":
            lines.append(f"| {name} | {left:.6%} | {right:.6%} |")
        else:
            lines.append(f"| {name} | {left:.6f} | {right:.6f} |")
    lines.extend(
        [
            "",
            "## Artifacts",
            f"- PnL comparison plot: `{pnl_plot_path.name}`",
            f"- Inventory comparison plot: `{inventory_plot_path.name}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _save_comparison_plot(ts_left: pd.DataFrame, ts_right: pd.DataFrame, path: Path, column: str, title: str) -> None:
    plt.figure(figsize=(12, 6))
    if not ts_left.empty:
        plt.plot(ts_left["timestamp"], ts_left[column], label="AS2008")
    if not ts_right.empty:
        plt.plot(ts_right["timestamp"], ts_right[column], label="MicropriceAS")
    plt.title(title)
    plt.xlabel("Timestamp (ns)")
    plt.ylabel(column)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()
