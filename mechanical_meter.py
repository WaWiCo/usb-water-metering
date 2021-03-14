##############################################
# Measuring water flow with mechanical flow
# meter for comparison against WaWiCo Acoustic
# flow detection
#
# -- by WaWiCo 2021
# 
##############################################
#
import time,sys,signal
import RPi.GPIO as gpio
#
#####################################
# Functions for handling interrupt
#####################################
#
def signal_handler(sig,frame):
    gpio.cleanup()
    sys.exit(0)

def sensor_callback(chan):
    global counter
    counter+=1

if __name__== '__main__':
    #####################################
    # Experiment Parameter Setup
    #####################################
    #
    t_elapsed = 0.1 # time [s] between each flow rate calculation

    counter = 0 # for counting and calculating frequency

    Q_prev = 0.0 # previous flow calculation (for total flow calc.) [L/s]

    conv_factor = 1.0/(5.5*60) # conversion factor to [L/s] from freq [1/s or Hz]
    vol_approx = 0.0 # initial approximation of volume [L]
    vol_prev   = 0.0 # for minimizing the prints to console
    
    #####################################
    # GPIO setup for interrupt
    #####################################
    #
    sensor_gpio = 17 # sensor GPIO pin
    gpio.setmode(gpio.BCM) # set for GPIO pin configuration
    gpio.setup(sensor_gpio,gpio.IN,pull_up_down=gpio.PUD_UP) # set interrupt
    #
    #####################################
    # Interrupt setup
    #####################################
    #
    gpio.add_event_detect(sensor_gpio,gpio.FALLING,callback=sensor_callback,
                          bouncetime=1) # setup interrupt for event detection 
    signal.signal(signal.SIGINT,signal_handler) # asynchronous interrupt handler
    #
    #####################################
    # Loop for approximating flow rate [L/s]
    # and total fluid accumulated [L]
    #####################################
    #
    t0 = time.time() # for updating time between calculations
    while True:
        if (time.time()-t0)<t_elapsed:
            pass
        else:
            Q = (conv_factor*(counter/t_elapsed)) # conversion to [Hz] then to [L/s]
            vol_approx+=(t_elapsed*((Q+Q_prev)/2.0)) # integrate over time for [L]
            counter = 0 # reset counter
            t0 = time.time() # get new time
            Q_prev = float(Q) # set previous rate
            if vol_approx!=vol_prev:
                print("Volume Approximation: {0:2.2f} L".format(vol_approx))
            vol_prev = float(vol_approx)
