
#   Create a threading event to be used as Flag for communication between threads in python
 #   Instantiate a Bokeh web document as webVisual, which is defined in Visual.py file
 #   Instantiate our Sensor thread and run it
#    For callback and interactive user experience:
 #       Feed the threads function into webVisual object to restart the thread from browser interface
  #      Feed the Bokeh document webVisual into our thread to enable the Sensor thread to inform the browser whenever new sensor data is available for plotting
  #      Feed the threading event Flag to both the Sensor thread and webVisual as a common Flag




from Visual import Visual
from SensorV2 import *
from Forecaster import Forecaster

def threads(callbackFunc, running):
    # Set multiple threads
    sensor = Sensor(callbackFunc=callbackFunc, running=running) # Instantiate the Sensor thread
    forecaster = Forecaster(sensor=sensor, visual=callbackFunc) # Instantiate the ARIMA Forecaster thread
    
    # Start threads 
    sensor.start() # Run the thread to start collecting data
    forecaster.start_forecasting()

def main():
    #Set global flag
    event = threading.Event() # Create an event to communicate between threads
    event.set() # Set the event to True

    webVisual = Visual(callbackFunc=threads, running=event) # Instantiate a Bokeh web document
    threads(callbackFunc=webVisual, running=event) # Call Sensor and forecaster threads

# Run command:
# bokeh serve --show streamingLab

main()
