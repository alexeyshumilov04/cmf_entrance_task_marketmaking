from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backtester.config import load_config
from backtester.engine import BacktestEngine
from backtester.reporting import save_comparison_report, save_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AS2008 vs MicropriceAS comparison")
    parser.add_argument("--config", default="configs/default.yaml", help="Base config for both variants")
    return parser.parse_args()


def run_variant(project_root: Path, config_path: Path, strategy_name: str, suffix: str) -> tuple[dict[str, float], pd.DataFrame]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw["strategy"]["strategy"] = strategy_name
    raw["output"]["output_dir"] = f"reports/{suffix}"

    tmp_config = project_root / "configs" / f"tmp_{suffix}.yaml"
    tmp_config.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    cfg = load_config(tmp_config)

    metrics = BacktestEngine(cfg, project_root).run()
    save_outputs(cfg, project_root, metrics)
    tmp_config.unlink(missing_ok=True)
    return metrics.summary_metrics(), metrics.timeseries_df()


def main() -> None:
    args = parse_args()
    project_root = PROJECT_ROOT
    config_path = (project_root / args.config).resolve()
    summary_as, ts_as = run_variant(project_root, config_path, "as2008", "as2008")
    summary_mp, ts_mp = run_variant(project_root, config_path, "microprice_as", "microprice_as2018")
    save_comparison_report(
        report_path=project_root / "reports" / "comparison_report.md",
        ts_as2008=ts_as,
        ts_microprice=ts_mp,
        summary_as2008=summary_as,
        summary_microprice=summary_mp,
    )
    print("Experiments completed. Check reports/as2008, reports/microprice_as2018 and reports/comparison_report.md")


if __name__ == "__main__":
    main()
