# PLAN.md - Phase 2: Configuration Externalisation

## Context & Objective
The LabVariab system currently hardcodes hardware addresses, scale coefficients, loop ranges, and system constraints straight into Python scripts (specifically in `34970A_5.py` and `SensorV2.py`). This is a bad pattern that prevents easy maintenance and deployment across different lab setups. The goal of this phase is to move all such configurations into a structured `config.ini` file and adapt the necessary layers to load parameters dynamically using the standard `configparser` package.

## Planned Steps

1. **Step 1: Create the Standard `config.ini` Template**
   * Target File: `config.ini` in the project root.
   * Details: Must include specific sections for:
     * `[HARDWARE]`: GPIB address, timeout.
     * `[LOGGING]`: Wait times, loop ranges.
     * `[CALIBRATION]`: Physical shunt value, amp min/max.
     * `[SENSORS]`: Channels setup (101-104) and scaling names.

2. **Step 2: Update `34970A_5.py` to use Configuration**
   * Action: 
     * Implement `configparser.ConfigParser()` initialization.
     * Replace constant hardcodes (`amp_min, amp_max = 4, 20`, `slicef = 10000`, `unit_scale = 1e3`, `shunt = 268`) with `.getint()`, `.getfloat()`.
     * Replace the hardcoded `rm.open_resource('GPIB0::5::INSTR')`.
     * Test the logger code to verify successful script boot sequence.

3. **Step 3: Update `SensorV2.py` and Associated Sub-Modules**
   * Provide unified configs via `config.ini` for anything exposed in `SensorV2.py` if present (e.g. data interval mapping or default visual values) prior to Milestone 2 & 3.

## Verification
* Execute a short test loop of `34970A_5.py` or inspect properties printout to ensure all variables imported correctly match pre-config equivalents.
