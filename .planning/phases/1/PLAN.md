# PLAN.md - Phase 1: Critical Robustness Patches

## Context & Objective
The GPIB logger `34970A_5.py` and its XML companion `TestcodeLogging34970A_v2.py` have runtime anti-patterns that prevent unsupervised 24/7 execution. The goal of this phase is to fix these specific critical bugs while validating the `safe_parse_scientific` logic against the Agilent manual specifications.

## Planned Steps

1. **Step 1: Fix Unary Typo in Retry Counter**
   * File: `streamingLab/TestcodeLogging34970A_v2.py`
   * Action: Change `ntries=+1` to `ntries += 1` inside the `for retry in range(50)` loop.

2. **Step 2: Remove Unreachable Return/Exit Logic**
   * File: `streamingLab/TestcodeLogging34970A_v2.py`
   * Action: Remove the dead code `sys.exit(1)` and the extraneous `break` occurring after the `return rha, tca, rhb, tcb, timestamp` statement, ensuring clean function exit.

3. **Step 3: Fix `NameError: datetime` in `safe_parse_scientific` Error Path**
   * File: `34970A_5.py` (and `streamingLab/Configura_34970A-14082024.py` if present)
   * Action: Change `datetime.now().isoformat()` to `dtime.now().isoformat()` inside the `except ValueError:` block, since the module is imported natively as `from datetime import datetime as dtime`.

4. **Step 4: Audit SCPI Scale Factor `* 10`**
   * File: `34970A_5.py`
   * Action: Inspect the `* 10` multiplier in `safe_parse_scientific`. According to the Agilent 34970A manual, `FETCH?` returns standard scientific notation (e.g., `+1.23E+00`). Verify if this `* 10` is intended to scale Volts to custom logical units (mA), add comments clarifying this exact metric based on the `Shunt = 268` math, and leave it if statistically correct for the calibration.

5. **Step 5: Fix Empty Strings Breaking List Dicts**
   * File: `34970A_5.py`
   * Action: Update `decode_to_dict()` mapping logic to defensively handle situations where the raw split array does not length-match the `dictprop` keys (e.g., upon full GPIB timeout returning `''`), averting `IndexError`.

## Verification
* Run the logging script in a short burst to confirm values process normally.
* Send an explicit mock string (e.g., `"2.82E"`) through `safe_parse_scientific` to confirm it prints the error gracefully without throwing `NameError`.
