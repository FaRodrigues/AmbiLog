
echo Conda env activation

call activate freq

echo started env properly for the jobs...


echo openning Data plottings, wait a moment...

bokeh serve --show streamingLab --port 502
pause
