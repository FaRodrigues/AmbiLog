# PLAN.md - Phase 4: Bokeh Sensor Buffer Logic

## Context & Objective
Currently, `SensorV2.py` reads a single data point from the XML datalogger and acts strictly as a pass-through, firing it directly to the UI (`Visual.py` via `self.callbackFunc.update`). While the UI handles a basic visual `rollover` using Bokeh’s `ColumnDataSource.stream`, the backend (`SensorV2.py`) has no concept of historical continuity. 
To enable forecasting algorithms like ARIMA (Phase 6), the system needs a persistent chunk of short-term historical context loaded in memory independently of what the UI decides to plot. Phase 4 introduces a localized memory buffer using `collections.deque` into `SensorV2.py` to continuously hold the recent history safely in background threads.

## Planned Steps

1. **Step 1: Buffer Sizing and Definition**
   * Edit `config.ini` to introduce a parameter for defining the background buffer length based on time (e.g., `buffer_size_elements = 120`). Since evaluations assume ~1 scan per 30 seconds, 120 slots equal exactly 1 hour of memory depth available to mathematical background processes without disk reads.

2. **Step 2: Buffer Instantiation (SensorV2.py)**
   * Target File: `streamingLab/SensorV2.py`
   * Import `collections.deque`.
   * Modify the constructor `__init__` to instantiate the deque structure. A dictionary holding fixed-size `deque` instances for each dimension: `timestamp`, `tempa`, `tempb`, `rha`, `rhb`, and uncertainties is appropriate. Also initialize thread locks if threading concurrency is deemed critical for retrieval, though a non-mutating `get()` clone typically suffices.

3. **Step 3: Update Mechanism**
   * Within `Sensor.run()`, successfully append the newly parsed, uncorrupted data to our local deque structure immediately before or after calling `self.callbackFunc.update(...)`.
   * Create an accessor method `get_buffer()` that returns lists of the deques (like `list(self.buffer['tempa'])`), so later phases can effortlessly invoke it to fit the models.
   * Add debug logs (via Python `logging`) to output the buffer size occasionally if required or confirm memory stability.

## Verification
* Unit checks on list allocation limits.
* Visual code review over the threading implications (using deque guarantees thread-safe append/pop in CPython, but we should verify the `get_buffer` clones the arrays quickly).
