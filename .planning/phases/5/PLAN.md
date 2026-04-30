# PLAN.md - Phase 5: GUM 95% Confidence Band (VIS-01)

## Context & Objective
The original v0.5 iteration of the visualization logic (`streamingLab/Visual.py`) introduced discrete vertical error bars (using `p.segment()`) to signify the real-world statistical uncertainties derived from hardware calibration sheets (GUM). 
However, for an environmental timeseries monitoring dashboard, vertical error bars at every point create visual clutter and obscure trends, especially when `rollover` accumulates hundreds of points.
Phase 5 addresses this by refactoring the `segment` elements into Bokeh's continuous `varea` (Vertical Area) renderer. This will create a smooth, semi-transparent confidence band (or envelope) behind the main data curve, allowing easier readability of 95% intervals without degrading the dashboard's "premium dynamic design" aesthetics.

## Planned Steps

1. **Step 1: Replace Segment Renderers**
   * Target File: `streamingLab/Visual.py`
   * Detail: Remove the `p.segment` calls representing uncertainties.
   * Instead, insert `p.varea(x='DateTime', y1='<param>_lower', y2='<param>_upper', source=source, fill_alpha=0.2, fill_color='<colour>')` calls for all 4 sensor channels (`y1`, `y2`, `y3`, `y4`).
   * Choose aesthetically pleasing layout colors that match the fundamental series (e.g., `firebrick` line gets a light red/gray varea).

2. **Step 2: Maintain Legend Hierarchy**
   * Link the newly created continuous band glyphs to the Bokeh legend structure, or maintain them decoupled under the existing sensor titles so `Legend.click_policy = "hide"` will hide both the line and band logically.

3. **Step 3: Verification & Execution Testing**
   * Review code syntax and initialization calls for `varea`, confirming Bokeh APIs (`y1` and `y2` parameters instead of `y0, y1`).

## UI / UX Benefits
- Transitions the discrete error representation into a mathematically sound "Confidence Tube" that moves organically in real-time, matching LabVariab's visual progression milestones and GUM normative presentation limits.
