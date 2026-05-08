# Performance Report: HFT Market Making Strategies (Python)

## 1. Data Description

**Instrument:** Cryptocurrency token (spot market)  
**Period:** August 1-7, 2024  
**Data source:** Level-2 order book snapshots + trade tape

| Dataset | Records | Description |
|---|---:|---|
| `lob.csv` | 1,036,690 | Order book snapshots, top-25 levels |
| `trades.csv` | 21,864,989 | All executed trades |

**Price dynamics:**
- Start price: ~0.01104
- End price: ~0.00774
- Total move: about -30% (strong downtrend)

`local_timestamp` is treated as nanoseconds in all calculations.

---

## 2. Model Description

### 2.1 Avellaneda-Stoikov (2008)

Reference: *High-frequency trading in a limit order book*, Avellaneda & Stoikov (2008).

Reservation price:
```
r = s - q * gamma * sigma^2 * (T - t)
```

Optimal spread:
```
delta = gamma * sigma^2 * (T - t) + (2/gamma) * ln(1 + gamma/kappa)
```

Quotes:
```
bid = r - delta/2
ask = r + delta/2
```

### 2.2 Microprice + Avellaneda-Stoikov (2018 extension)

Reference: *The micro-price: A high frequency estimator of future prices*, Stoikov (2018).

Microprice proxy:
```
microprice = ask * (bid_vol / (bid_vol + ask_vol)) + bid * (ask_vol / (bid_vol + ask_vol))
```

The strategy uses this microprice instead of plain mid-price inside Avellaneda-Stoikov equations.

---

## 3. Backtesting Engine

- Event stream is built by merging `lob.csv` and `trades.csv` by `local_timestamp`.
- At most one active bid and one active ask order are kept.
- On each LOB event:
  - fair price and quotes are recomputed
  - old orders are canceled
  - new two-sided quotes are placed
- Execution rule:
  - if `trade.side == sell` and `trade.price <= bid_order.price`, buy order is filled
  - if `trade.side == buy` and `trade.price >= ask_order.price`, sell order is filled
- Partial fills are supported:
  - order remaining size is decreased by `trade.amount`
  - overflow trade volume is ignored after order reaches zero
- Fees and slippage are disabled.

---

## 4. Metrics

For each strategy the project computes:
- Final MtM PnL
- Final inventory
- Turnover
- Annualized Sharpe ratio (risk-free = 0):
  - scaling: `sqrt(252 * 6.5 * 3600 / total_duration_seconds)`
- Maximum drawdown (absolute, in PnL units)
- Maximum drawdown duration (seconds)
- Hit-rate:
  - `profitable_trades / all_non_zero_trades`

---

## 5. Output Artifacts

Single strategy run (`run_backtest.py`) creates:
- `reports/performance_report.md`
- `reports/metrics_timeseries.csv`
- `reports/fills.csv`
- `reports/pnl_inventory.png`
- `reports/inventory_over_time.png`

Comparison run (`scripts/run_experiments.py`) creates:
- `reports/as2008/*`
- `reports/microprice_as2018/*`
- `reports/comparison_report.md`
- `reports/comparison_pnl.png`
- `reports/comparison_inventory.png`

---

## 6. Installation

```powershell
cd "d:\Development\Projects\CMF\python_backtester"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

---

## 7. Usage

Run one strategy from config:

```powershell
python run_backtest.py --config configs/default.yaml
```

Run two-strategy comparison (AS2008 vs MicropriceAS):

```powershell
python scripts/run_experiments.py --config configs/default.yaml
```

Quick smoke run:

```powershell
python run_backtest.py --config configs/quick_smoke.yaml
python scripts/run_experiments.py --config configs/quick_smoke.yaml
```

---

## 8. Repository Structure

- `run_backtest.py` - single strategy runner
- `scripts/run_experiments.py` - comparative experiment runner
- `configs/default.yaml` - full-data config
- `configs/quick_smoke.yaml` - reduced quick-run config
- `src/backtester/engine.py` - backtesting loop
- `src/backtester/strategy.py` - AS2008 and MicropriceAS implementations
- `src/backtester/data.py` - data loading and event merge
- `src/backtester/metrics.py` - metric computations
- `src/backtester/reporting.py` - reports and plots

---

## 9. Improvement Roadmap

1. Calibrate `gamma` and `kappa` from data (regime-aware).
2. Add maker/taker fees and slippage model.
3. Add queue-position execution model.
4. Add adaptive order size based on inventory and volatility.
5. Add walk-forward validation and parameter sensitivity analysis.
