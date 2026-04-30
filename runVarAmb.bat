@echo off

echo Running Ambient Variables plotting for Laboratory using 34970A sensor

echo Conda env activation

call activate freq

echo started env properly for the jobs...

echo starting sensor data logging

python 34970A_5.py

pause