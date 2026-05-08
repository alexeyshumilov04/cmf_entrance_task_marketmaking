# Performance Report

## Strategy
- Name: `microprice_as`
- gamma: `0.01`
- kappa: `1.5`
- horizon_seconds: `3600.0`
- q_max: `50000.0`
- order_size: `1000.0`
- vol_window: `50`

## Core Metrics
- Final MtM PnL: `0.335456`
- Final Inventory: `-2000.000000`
- Turnover: `1258.299456`
- Sharpe Ratio (annualized, rf=0): `63.185764`
- Max Drawdown (absolute PnL): `0.286048`
- Max Drawdown Duration (sec): `1.099953`
- Hit-rate: `49.315068%`
- Total Duration (sec): `10.130667`
- Number of Buy Fills: `74`
- Number of Sell Fills: `72`

## Notes
- Backtest processes merged `lob.csv` and `trades.csv` events by `local_timestamp`.
- Engine uses up to one active bid and one active ask order.
- Partial fill logic is enabled.
- No fees and no slippage are applied.
