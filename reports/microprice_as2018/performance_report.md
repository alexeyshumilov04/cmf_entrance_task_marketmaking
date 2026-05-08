# Performance Report

## Strategy
- Name: `microprice_as`
- gamma: `0.01`
- kappa: `1.5`
- horizon_seconds: `520.0`
- q_max: `50000.0`
- order_size: `1000.0`
- vol_window: `50`

## Core Metrics
- Final MtM PnL: `-31.279409`
- Final Inventory: `24015.000000`
- Turnover: `672626.718707`
- Sharpe Ratio (annualized, rf=0): `-3.891265`
- Max Drawdown (absolute PnL): `51.505335`
- Max Drawdown Duration (sec): `396.046498`
- Hit-rate: `50.147105%`
- Total Duration (sec): `517.897949`
- Number of Buy Fills: `51173`
- Number of Sell Fills: `51475`

## Notes
- Backtest processes merged `lob.csv` and `trades.csv` events by `local_timestamp`.
- Engine uses up to one active bid and one active ask order.
- Partial fill logic is enabled.
- No fees and no slippage are applied.
