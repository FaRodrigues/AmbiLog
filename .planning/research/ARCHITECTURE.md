# ARCHITECTURE.md — Architecture Research: LabVariab v0.6

## Current Architecture (v0.5)

```
34970A_5.py (Logger)          streamingLab/ (Bokeh)          VarAmbseries0.6.2.py
     │                              │                                │
GPIB → SCPI → XML             XML → Thread → Bokeh            XML → Tkinter + matplotlib
     │                              │                                │
./varamblog/{YYDDD}/*.xml ←────────┴────────────────────────────────┘
```

## How v0.6 Features Integrate

### Feature 1: 95% CI Band (Dashboard)

```
SensorV2.Sensor.run() [every 30s]
  ├── varsall = Datalog.list_file()
  ├── Compute err_tempa, err_tempb, err_rha, err_rhb (ALREADY DONE ✓)
  │
  └── [NEW] Maintain ring buffer: last N=120 readings (1h @ 30s)
        └── Compute rolling GUM: mean(y) ± k * u_c(rolling)
              └── doc.add_next_tick_callback(partial(Visual.update_band, ...))
                    └── Band glyph upper/lower ColumnDataSource
```

**Key decision**: Where does the band state live?
- Option A: In `Sensor` thread (simple but couples data + stats)
- Option B: Separate `StatsWorker` class (cleaner but more complex)
- **Recommendation**: Option A — stateful ring buffer inside `Sensor`, consistent with existing pattern

### Feature 2: ARIMA 30-min Forecast

```
SensorV2.Sensor.run() [every 30s]
  ├── [NEW] refit_counter += 1
  │       if refit_counter % 10 == 0:  # every 5 min
  │           arima_model = ARIMA(ring_buffer_T, order=auto_order).fit()
  │           forecast = arima_model.forecast(steps=6)  # 6 × 30s = 3 min
  │           [Actually: 6 steps × 30s = 3 min... wait]
  │           [For 30 min: need 60 steps × 30s]
  │           forecast = arima_model.forecast(steps=60)
  │           forecast_ci = arima_model.get_forecast(steps=60).conf_int(alpha=0.05)
  │
  └── doc.add_next_tick_callback(partial(Visual.update_forecast,
          forecast_T, forecast_T_lower, forecast_T_upper,
          forecast_RH, forecast_RH_lower, forecast_RH_upper,
          forecast_times))
```

**ARIMA fit frequency**: Every 10 readings (5 min) to avoid CPU saturation
**Forecast horizon**: 60 steps × 30s = 30 minutes ✓
**Minimum data for fit**: ≥30 readings (15 min of data)
**ARIMA order selection**: 
  - Auto: `pmdarima.auto_arima()` (adds `pmdarima` dependency)
  - Manual: ARIMA(2,0,1) as default — sensible for smooth T/RH series
  - **Recommendation**: Start with fixed ARIMA(2,0,1) + user-configurable in config.ini

### Feature 3: Config Externalization

```
config.ini [new file]
  ├── [instrument] gpib_address, timeout_ms, channels
  ├── [calibration] shunt_ohm, amp_min, amp_max, nplc, scan_interval
  ├── [dashboard] bokeh_port, rollover, poll_interval_s
  ├── [forecast] arima_p, arima_d, arima_q, horizon_steps, refit_every
  └── [logging] log_file, log_level, max_bytes, backup_count

34970A_5.py → reads config.ini at startup
streamingLab/SensorV2.py → reads config.ini (dashboard params, forecast params)
```

### Feature 4: Logger Stability (Bug Fixes)

No architectural change — targeted fixes:
1. `safe_parse_scientific`: fix `datetime` reference → use `dtime`
2. `ntries=+1` → `ntries += 1`
3. XML retry loop: move `tree = ET.parse()` INSIDE the retry loop
4. Validate `* 10` factor (likely: SCPI returns mA×10 scale, so ×10 = mV; confim with manual)
5. Replace `print()` with `logging`

## Build Order (Phase Dependencies)

```
Phase 1: Bug fixes + config externalization (STAB)
  └── Phase 2: Logging module + requirements.txt
        └── Phase 3: 95% CI Band in Bokeh
              └── Phase 4: ARIMA forecast engine
                    └── Phase 5: Visual integration (forecast line + band in Visual.py)
                          └── Phase 6: VarAmbseries enhancement (historical + forecast)
                                └── Phase 7: Integration tests + deployment cleanup
```

## Fragile Areas to Handle Carefully

| Area | Risk | Mitigation |
|------|------|-----------|
| ARIMA in Bokeh thread | CPU spike blocks 30s loop | Fit in thread, cache model between refits |
| ColumnDataSource.stream() thread safety | Race condition | Always use `add_next_tick_callback` |
| XML parse during logger write | Truncated file | ETParseError retry (already handled) |
| GPIB timeout during model refit | Compound delay | Sequence: read GPIB → release → then fit ARIMA |
| Day rollover + ring buffer | Buffer spans two XML files | Ring buffer keyed by timestamp, not filename |
