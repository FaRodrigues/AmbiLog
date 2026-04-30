@echo off

echo Running Ambient Variables plotting for Laboratory using 34970A sensor

echo Conda env activation

call activate freq


echo openning Temporal series analyses, wait a moment...

python VarAmbseries0.6.2.py

pause