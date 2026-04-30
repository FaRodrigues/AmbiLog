@echo off
echo Starting LabVariab Program v0.6.2
echo Authors: F.Rodrigues, Marcelo De Cicco. 2024-2026
echo.
echo Phase 8: Hardened Path Integrations & Predictive UI
echo.

echo [1/3] Starting Sensor Logger (34970A)...
start cmd /k runVarAmb.bat

echo Waiting 15s for sensor stabilization...
timeout /t 15

echo [2/3] Starting Real-Time Bokeh Dashboard...
start cmd /k runVarAmb2.bat

echo [3/3] Starting Historical Series Analyzer...
start cmd /k runVarAmbSeries.bat

echo.
echo All modules started successfully!
timeout /t 5
exit
