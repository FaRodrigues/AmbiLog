# PLAN.md - Phase 7: UI Premium Aesthetics & Pipeline Robustness

## Context & Objective
At the end of Phase 6, we successfully deployed an advanced predictive data architecture matching mathematical expectations. However, to comply fully with the agent interface directives for premium aesthetic standards, the Bokeh dashboard requires a visual upgrade (`UI-01`). Currently, the layout employs a standard white background with native browser CSS controls, which contradicts the rich aesthetics "dark mode, vibrant colors" directive.
Additionally, we need to enforce data pipeline reliability (`PIPLN-01`) for long-term experimental runs where Agilent hardware or network shares might briefly disconnect and return empty data structures.

## Planned Steps

1. **Step 1: Premium Dark Theme Implementation (`Visual.py`)**
   * Activate the native Bokeh `dark_minimal` theme or configure document `theme_from_json()` to achieve a sleek, premium dark appearance (avoiding standard blinding bright modes).
   * Refactor the title `Div(text="<h1>...")` CSS: inject inline modern web design traits (e.g., sans-serif geometric fonts like Inter/Roboto, soft dropshadows, or a subtle gradient header text).
   * Restyle grid lines and axes lines in `definePlot()` with lower opacity to prevent clash with the "neon-like" prediction vectors.

2. **Step 2: Streamlined Layout Adjustments**
   * Enhance spacing and margins in the layout: `row()` and `column()` components should utilize the `sizing_mode="stretch_width"` to become responsive instead of a rigid 1200px block.
   * Format the Button controls (`Toggle`, `CheckboxGroup`) via embedded inline CSS styles inside the `Div` blocks or relying on Bokeh's built-in button styles (e.g., `primary`, `success`) matched to dark mode contrasts.

3. **Step 3: Reliability Wrappers (`SensorV2.py` / `TestcodeLogging34970A_v2.py`)**
   * Confirm that disconnected state (missing XML drops) is signaled visually. If data goes flat for > N cycles, inject a "NaN" timestamp or handle the UI error boundary without crashing the Python thread.
   * Add a `try/finally` around the `Forecaster` and `Sensor` `run()` loops to ensure system cleanly releases resources if interrupted by the console.

## UI / UX Benefits
- Implements state-of-the-art interface aesthetics requested on standard guidelines, enhancing presentation during technical reporting or monitoring.
- Provides a sense of responsive "liveness", shifting from a rudimentary plotting script into an industrial-grade enterprise dashboard look.
