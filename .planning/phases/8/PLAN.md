# PLAN.md - Phase 8: Hardened Path Integrations & Historical UI

## Context & Objective
The user has reverted `varamblog` to its original root location (`Scripts/WinVer/0.5/7/varamblog`). Consequently, Phase 8 adjusts its scope: instead of tracking a moved folder, we will implement **Absolute/Dynamic Relative Pathing** (via `__file__`) in all python modules (`SensorV2.py`, `Datalog`, and the `AmbSeries` historical app). This ensures that whether the user clicks a `.bat` file on the desktop or runs via IDE, the path to `varamblog` will never break.
We will also audit the new Tkinter historical UI (`VarAmbseries0.6.2.py`) to confirm it extracts data without flaws.

## Planned Steps

1. **Step 1: Bulletproof Path Resolution (`TestcodeLogging34970A_v2.py` e `SensorV2.py`)**
   * Change constructor logic from `vars_reader = Datalog('.')` to use explicit `os.path` combinations ensuring it always looks at `../varamblog` (relative to the `streamingLab` script location) regardless of the terminal's *Current Working Directory*.

2. **Step 2: Auditoria do App Histórico (`AmbSeries/VarAmbseries0.6.2.py`)**
   * Inspect the historical analyzer to confirm it also employs bulletproof pathing to the root `varamblog`. 
   * Verify if the Tkinter components properly load the data structures without syntax errors resulting from our 0.5 / 0.6 version bump.

3. **Step 3: Verification of Batch Execution Scripts (.bat)**
   * Ensure `runVarAmb2.bat`, `runMain.bat`, and `runVarAmbSeries.bat` correctly point to the updated python script filenames.

## Delivery State (Definition of Done)
- The application executes independently of the terminal's `.pwd`, accurately loading logs from the root `varamblog`.
- Batch scripts directly spawn the Tkinter UI and Bokeh Servers without path crashes.
