# PLAN.md - Phase 6: ARIMA / Markov Forecasting (PRED-01)

## Context & Objective
The user has requested the capability to predict the future state of the lab's environmental variables (Temperature and Humidity) for the next 30 minutes, showing a 95% confidence bounds around the projected data. The requirement mentions using an adaptation of Markov chains and the previously established `statsmodels` library (which has ARIMA).
Since a first-order autoregressive process AR(1) natively assumes the Markov property (the next state depends entirely on the current state), we will configure an ARIMA model to act as a generalized continuous-time Markov forecasting process.

## Planned Steps

1. **Step 1: Forecasting Engine Development (`Forecaster.py` ou expansão do `SensorV2.py`)**
   * Write an asynchronous routine that periodically triggers the forecasting engine. Because computing ARIMA on 120 buffer samples may take a few seconds and block the UI or data acquisition, it must run via `asyncio.to_thread` or in a separate background thread.
   * Fetch the locked historical data snapshot `sensor.get_buffer()`.
   * For each channel (`y1`, `y2`, `y3`, `y4`), fit an ARIMA model, e.g., `ARIMA(endog, order=(1,1,0))` (AR=1 guarantees the Markov property mathematically).
   * Perform an out-of-sample forecast for `h = 30 minutes` (60 ticks if scan interval is 30s).
   * Extract both the forecasted values and the 95% prediction intervals from the statistical model.

2. **Step 2: Prediction ColumnDataSource Integration (`Visual.py`)**
   * Create a new Bokeh `ColumnDataSource` (e.g., `pred_source`) specialized for storing the future trajectory points (`pred_datetime`, `pred_y1`, `pred_y1_lower`, `pred_y1_upper`, etc.).
   * In `update()`, check if the forecasting engine has fresh data available. If it exists, update `pred_source`.
   * Render the forecast using `p.line(..., line_dash="dashed")` to clearly indicate it's predictive, avoiding confusion with actual readings.
   * Render the 95% forecasting interval using `p.varea(...)` with a more transparent or distinct fill color (e.g., `fill_alpha=0.1`).

3. **Step 3: Execution Controls & Configuration**
   * Add a `Forecast_Interval_Seconds` control to ensure we don't recalculate the 30-minute Markov chain heavily on every UI frame. Example: Recalculate predictions every 1 a 5 minutos.
   * Ensure any NaN or initialization states skip prediction gracefully until the `SensorV2` buffer has sufficient data (e.g., at least 20 points).

## UI / UX Benefits
- Moves the system beyond monitoring ("What is happening?") into prescriptive analysis ("What will happen to the experiment in half an hour?").
- Retains aesthetic unity by reusing Bokeh's varea to denote statistical spread, matching the real data's GUM confidence bands.
