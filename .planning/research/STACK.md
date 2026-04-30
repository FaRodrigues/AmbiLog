# STACK.md — Stack Research: LabVariab v0.6
<!-- Research: subsequent milestone (adding forecast + CI + robustness to existing Python/Bokeh/pyvisa system) -->

## Current Stack (Confirmed Existing)

| Component | Version Constraint | Status |
|-----------|-------------------|--------|
| Python | ≥ 3.7 (docstring), ≥ 3.8 recommended | ✅ Conda env `freq` |
| pyvisa | ≥ 1.11 (VisaIOError API) | ✅ |
| numpy | ≥ 1.20 | ✅ |
| sympy | ≥ 1.8 | ✅ |
| astropy | ≥ 4.0 | ✅ |
| bokeh | ≥ 2.4 (TabPanel API used) | ✅ |
| pandas | ≥ 1.3 | ✅ |
| matplotlib | ≥ 3.4 | ✅ |
| tkinter | stdlib | ✅ |

## Additions Needed for v0.6

### ARIMA Forecast (30-min) — `statsmodels`
- **Package**: `statsmodels` ≥ 0.13
- **Class**: `statsmodels.tsa.arima.model.ARIMA`
- **Rationale**: Recommended over Markov for continuous scalars (T, RH) per Stat2Science
- **Alternative considered**: `scikit-learn` LinearRegression / ARModel — simpler but less statistically rigorous
- **Confidence**: HIGH — statsmodels is the standard Python TSA library, well-maintained
- **Forecast window**: AR(3) or ARIMA(2,0,1) — to be validated against actual data at runtime
- **What NOT to use**: Prophet (Facebook) — overkill for 30-min horizon; complexity not justified

### Configuration Management — stdlib solution
- **Package**: `configparser` (stdlib, Python 3.2+) or `python-dotenv`
- **Decision**: `configparser` — already available, no new dependency, `.ini` format readable by non-programmers
- **Alternative**: `pyyaml` — more readable but extra dependency
- **Confidence**: HIGH

### Logging
- **Package**: `logging` (stdlib) — replace all `print()` statements in logger
- **Pattern**: `RotatingFileHandler` for production log files, `StreamHandler` for console
- **Confidence**: HIGH

### 95% Confidence Band in Bokeh
- **Method**: Rolling window → mean ± 1.96×std (frequentist) OR GUM expanded uncertainty band
- **Bokeh API**: `Band` glyph (`bokeh.models.Band`) with `ColumnDataSource` upper/lower
- **Decision**: Use rolling GUM-based band (propagation of u_c over window) to stay consistent with metrological framework — NOT naive ±2σ on raw data
- **Confidence**: HIGH — `Band` is stable Bokeh API since 1.x

### statsmodels ARIMA in Bokeh Thread
- **Challenge**: ARIMA fit is CPU-intensive for realtime — must run in background thread, not IOLoop
- **Pattern**: Fit in `Sensor` thread (already background), push forecast to `ColumnDataSource` via `add_next_tick_callback`
- **Model refit frequency**: Every 10 new data points (5 minutes at 30s interval) — balance between accuracy and CPU cost
- **Confidence**: MEDIUM — thread safety with Bokeh callbacks requires care

## What NOT to Change
- **Bokeh** — proven, already deployed. Don't switch to Plotly/Dash.
- **XML storage** — adequate for scale. Don't add DB.
- **pyvisa** — only viable GPIB Python interface.
- **Conda `freq` env** — don't migrate to bare pip venv yet.

## Missing Documentation to Generate
- `requirements.txt` (freeze from Conda env `freq`)
- `environment.yml` (full Conda export)
- `config.ini` (GPIB address, port, rollover, etc.)
