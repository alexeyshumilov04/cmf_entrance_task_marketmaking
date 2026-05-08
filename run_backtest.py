from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backtester.config import load_config
from backtester.engine import BacktestEngine
from backtester.reporting import save_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LOB backtest with AS strategies")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Path to YAML config")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    config = load_config(project_root / args.config)

    engine = BacktestEngine(config=config, project_root=project_root)
    metrics = engine.run()
    outputs = save_outputs(config=config, project_root=project_root, metrics=metrics)

    ts = metrics.timeseries_df()
    if ts.empty:
        print("No market data was processed.")
    else:
        final = ts.iloc[-1]
        print("Backtest completed.")
        print(f"Final MtM PnL: {final['mtm_pnl']:.6f}")
        print(f"Final Inventory: {final['inventory']:.6f}")
        print(f"Turnover: {final['turnover']:.6f}")
    print("Artifacts:")
    for key, path in outputs.items():
        print(f"- {key}: {path}")


if __name__ == "__main__":
    main()
