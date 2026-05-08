# Performance Report

## Strategy
- Name: `as2008`
- gamma: `0.01`
- kappa: `1.5`
- horizon_seconds: `520.0`
- q_max: `50000.0`
- order_size: `1000.0`
- vol_window: `50`

## Core Metrics
- Final MtM PnL: `-29.898460`
- Final Inventory: `24852.000000`
- Turnover: `675369.709220`
- Sharpe Ratio (annualized, rf=0): `-3.702611`
- Max Drawdown (absolute PnL): `48.352240`
- Max Drawdown Duration (sec): `340.040995`
- Hit-rate: `50.195087%`
- Total Duration (sec): `517.897949`
- Number of Buy Fills: `51442`
- Number of Sell Fills: `51845`

## Notes
- Backtest processes merged `lob.csv` and `trades.csv` events by `local_timestamp`.
- Engine uses up to one active bid and one active ask order.
- Partial fill logic is enabled.
- No fees and no slippage are applied.
