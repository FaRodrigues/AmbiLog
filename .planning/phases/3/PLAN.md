# PLAN.md - Phase 3: Packaging and Logging Standards

## Context & Objective
The LabVariab system currently uses unmanaged dependencies (implicit `freq` conda environment) and extensive raw `print()` statements for diagnostic and operational messages, which convolutes output management in production. This phase addresses reproducibility by exporting environments and establishes proper backend logging to files via python's native `logging` module so history is retained correctly without flooding shells.

## Planned Steps

1. **Step 1: Export Project Dependencies**
   * Target File: `requirements.txt` / `environment.yml`
   * Details: Execute Conda/Pip freeze commands for the active session or infer required libraries (like `pyvisa`, `bokeh`, `statsmodels`, `sympy`, `numpy`, `astropy`) to stub out base environment configuration.

2. **Step 2: Initialize Core System Logger**
   * Create a global logger utility script `logger_config.py` in `streamingLab/` that configures a `RotatingFileHandler` alongside a conventional standard output `StreamHandler`.
   * Standardize the output format to include `{asctime} - {levelname} - {message}`.

3. **Step 3: Refactor Raw Print Statements**
   * Target Files: `34970A_5.py`, `TestcodeLogging34970A_v2.py`, `SensorV2.py`
   * Details: Replace manual console messages like `print(f"[{dtime.now().isoformat()}] TIMEOUT VISA...")` with `logger.error(...)` or `logger.info(...)`. Drop the repetitive `[{dtime.now()}]` injection since the logger automatically applies timestamps.

## Verification
* Run code syntax check.
* Verify log file generation functionality.
