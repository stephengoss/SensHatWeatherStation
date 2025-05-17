#!/usr/bin/python
'''********************************************************************************************************************
   Pi Temperature Station
   Bassed on code orignaly By John M. Wargo www.johnwargo.com

   This is a Raspberry Pi project that measures weather values (temperature, humidity and pressure) using
   the Astro Pi Sense HAT then uploads the data to a Weather Underground weather station.
********************************************************************************************************************'''

from __future__ import print_function  # okay to keep for Python 2/3 compatibility
from sense_hat import SenseHat         # required for Sense HAT
from config import Config              # required for reading config values

import datetime                        # used for timestamping and control flow
import os                              # used to get CPU temp
import glob                            # used to find DS18B20 device folder
import sys                             # used for exception handling and exit
import time                            # used for delays and time comparisons
import requests                        # used to send HTTP request to WUnderground
import logging

'''*****************************************************************************************************************
   Constants

*****************************************************************************************************************'''

__version__ = "1.0.1"
base_dir = '/sys/bus/w1/devices/'
device_folder_check = glob.glob(base_dir + '28*')
temp_sensor = "SENSHAT"
symbol_sleep = 4   
BRIGHTNESS = 200

# constants used to display an up and down arrows plus bars
# modified from https://www.raspberrypi.org/learning/getting-started-with-the-sense-hat/worksheet/
# set up the colours (blue, red, empty)
b = [0, 0, 55 + BRIGHTNESS]  # blue
r = [55 + BRIGHTNESS, 0, 0]  # red
e = [0, 0, 0]   # empty
g = [0, 55 + BRIGHTNESS, 0]  # green

# create images for up and down arrows
arrow_up = [
    e, e, e, r, r, e, e, e,
    e, e, r, r, r, r, e, e,
    e, r, e, r, r, e, r, e,
    r, e, e, r, r, e, e, r,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e
]
arrow_down = [
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    b, e, e, b, b, e, e, b,
    e, b, e, b, b, e, b, e,
    e, e, b, b, b, b, e, e,
    e, e, e, b, b, e, e, e
]
bars = [
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    g, g, g, g, g, g, g, g,
    g, g, g, g, g, g, g, g,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
]
green_tick = [
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, g, e,
    e, e, e, e, e, g, e, e,
    e, e, e, e, g, g, e, e,
    g, e, e, g, g, e, e, e,
    e, g, g, g, e, e, e, e,
    e, g, g, g, e, e, e, e,
    e, e, g, e, e, e, e, e,
]
red_cross = [
    r, r, e, e, e, e, r, r,
    r, r, r, e, e, r, r, r,
    e, r, r, r, r, r, r, e,
    e, e, r, r, r, r, e, e,
    e, e, r, r, r, r, e, e,
    e, r, r, r, r, r, r, e,
    r, r, r, e, e, r, r, r,
    r, r, e, e, e, e, r, r,
]
'''*****************************************************************************************************************
   Functions

*****************************************************************************************************************'''
# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Formatter for both handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# --- Console handler ---
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# --- File handler ---
file_handler = logging.FileHandler('weather_station.log', mode='a')  # mode='w' to overwrite
file_handler.setLevel(logging.INFO)  # You can use a different level for the file
file_handler.setFormatter(formatter)

# --- Attach handlers if not already attached ---
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

if not device_folder_check:
    logger.info("No DS18B20 sensor found. Continuing with SENSHAT data.")
    temp_sensor = "SENSHAT"
else:
    # device_folder = glob.glob(base_dir + '28*')[0]
    logger.info("DS18B20 sensor found.")
    temp_sensor = "DS18B20"

def read_temp_raw():
    base_dir = '/sys/bus/w1/devices/'   
    device_folder = glob.glob(base_dir + '28*')[0]  # '28*' is the DS18B20 family code
    device_file = device_folder + '/w1_slave'
    with open(device_file, 'r') as f:
        return f.readlines()

def read_temp_DS18B20():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
        logger.debug("read_temp_DS18B20")
        logger.debug(lines)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def read_temp_sense():
    logger.info("read_temp_sense_hat no DS18B20 detected.") 
    return sense.get_temperature_from_pressure()
    
def read_temp():
    if temp_sensor == "DS18B20":
        return read_temp_DS18B20()
    else:
        return read_temp_sense()

def print_orientation():
    logger.info("print_orientation")
    north = sense.get_compass()
    logger.info("North: %s" % north)
    logger.info(sense.compass)
    orientation = sense.get_orientation()
    logger.info("p: {pitch}, r: {roll}, y: {yaw}".format(**orientation))
    logger.info(sense.orientation)
    return True

def set_low_light():
    logger.info("set_low_light")

    hour = time.localtime().tm_hour
    if 7 <= hour < 18:
        sense.low_light = False
        logger.info("low_light = False")
    else:
        sense.low_light = True
        logger.info("low_light = True")
    return True

def set_gamma():
    logger.info("set_gamma")
    sense.gamma_reset()
    logger.info('Gamma : ')
    logger.info(sense.gamma)
    sense.clear(255, 127, 0)
    return True

def set_brightness():
    logger.info("set_brightness")

    hour = time.localtime().tm_hour
    if 7 <= hour < 18:
        BRIGHTNESS = 200
        logger.info("day brightness = 200")
    else:
        BRIGHTNESS = 20
        logger.info("evening brightness = 20")
    return True

def display_red_arrow():
    logger.info("display_red_arrow")
    sense.set_pixels(arrow_up)
    time.sleep(symbol_sleep)
    return True

def display_blue_arrow():
    logger.info("display_blue_arrow")
    sense.set_pixels(arrow_down)
    time.sleep(symbol_sleep)
    return True

def display_bars():
    logger.info("display_bars")
    sense.set_pixels(bars)
    time.sleep(symbol_sleep)
    return True

def display_green_tick():
    logger.info("display_green_tick")
    sense.set_pixels(green_tick)
    time.sleep(symbol_sleep)
    return True

def display_red_cross():
    logger.info("display_red_cross")
    sense.set_pixels(red_cross)
    time.sleep(symbol_sleep)
    return True

def c_to_f(input_temp) -> float:
    """Convert input_temp from Celsius to Fahrenheit."""
    return (input_temp * 1.8) + 32

def get_cpu_temp() -> float:
    """Get the CPU temperature in Celsius."""
    try:
        res = os.popen('vcgencmd measure_temp').readline()
        return float(res.replace("temp=", "").replace("'C\n", ""))
    except Exception as e:
        logger.error(f"Failed to get CPU temperature: {e}")
        return float('nan')

def get_smooth(x) -> float:
    """Use moving average to smooth readings."""
    logger.info("x %d " % x)
    # do we have the t object?
    if not hasattr(get_smooth, "t"):
        # then create it
        get_smooth.t = [x, x, x]
    # manage the rolling previous values
    get_smooth.t[2] = get_smooth.t[1]
    get_smooth.t[1] = get_smooth.t[0]
    get_smooth.t[0] = x
    # average the three last temperatures
    xs = (get_smooth.t[0] + get_smooth.t[1] + get_smooth.t[2]) / 3
    logger.debug("smooth 0 : %d" % get_smooth.t[0])
    logger.debug("smooth 1 : %d" % get_smooth.t[1])
    logger.debug("smooth 2 : %d" % get_smooth.t[2]) 

    return xs

def get_temp() -> float:
    """approximation of the actual temp from the sens hat, taking CPU temp into account"""
    # Unfortunately, getting an accurate temperature reading from the
    # Sense HAT is improbable, see here:
    # https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
    # so we'll have to do some approximation of the actual temp
    # taking CPU temp into account. The Pi foundation recommended
    # using the following:
    # http://yaab-arduino.blogspot.co.uk/2016/08/accurate-temperature-reading-sensehat.html
    # First, get temp readings from both sensors
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    # t becomes the average of the temperatures from both sensors
    t = (t1 + t2) / 2

    # Now, grab the CPU temperature
    t_cpu = get_cpu_temp()

    logger.info("Humidiy temp  : %d" % t1)
    logger.info("Pressure temp : %d" % t2)
    logger.info("Average temp  : %d" % t)
    logger.info("CPU temp      : %d" % t_cpu)

    logger.info("read_temp")
    ds_temp = read_temp()

    # Calculate the 'real' temperature compensating for CPU heating
    t_corr = t - ((t_cpu - t) / 1.5)
    t_corr = ds_temp

    logger.info("t_corr : %d" % t_corr)
    # Finally, average out that value across the last three readings
    t_corr = get_smooth(t_corr)
    # convoluted, right?
    # Return the calculated temperature
    logger.info("Smoothed temp : %d" % t_corr)

    return t_corr

def main():
    global last_temp
    allIsGood = True
    displaySymbol = True
    displayText = True
    upload_on_change = True

    last_temp_c = 0

    print_orientation()
    set_gamma()
    set_brightness()
    set_low_light()

    # infinite loop to continuously check weather values
    while allIsGood:
        current_second = datetime.datetime.now().second

        if allIsGood:
            calc_temp = get_temp()
            temp_c = round(calc_temp, 1)
            temp_f = round(c_to_f(calc_temp), 1)
            humidity = round(sense.get_humidity(), 0)
            pressure = round(sense.get_pressure() * 0.0295300, 1)

            logger.info("Temp: %sc, Pressure: %s inHg, Humidity: %s%% Second:%s" % (temp_c, pressure, humidity, current_second))
            logger.info("displayText: %s, displaySymbol: %s" % (str(displayText), str(displaySymbol)))

            if displayText:
                sense.clear()
                sense.show_message(" " + str(temp_c) + "c ", text_colour=[55+BRIGHTNESS, 55+BRIGHTNESS, 0], back_colour=[0, 0, 0])
                sense.show_message(" " + str(temp_c) + "c ", text_colour=[55+BRIGHTNESS, 55+BRIGHTNESS, 0], back_colour=[0, 0, 0])

            if displaySymbol:
                sense.clear()
                if last_temp_c != temp_c:
                    if last_temp_c > temp_c:
                        # display_blue_arrow                        
                        logger.info("Temperature going DOWN")
                        display_blue_arrow()
                        upload_on_change = True
                    else:
                        # display_red_arrow
                        logger.info("Temperature going UP")
                        display_red_arrow()
                        upload_on_change = True
                else:
                    # display_bars
                    logger.info("Temperature is the SAME")
                    display_bars()
                    upload_on_change = False

            # set last_temp to the current temperature before we measure again
            last_temp_c = temp_c

            # set the brighness bassed on the time of day.
            set_brightness()
            set_low_light()
            last_temp = temp_f

            if wu_weather_upload:
                logger.info("Uploading data to Weather Underground")

                try:
                    upload_url = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

                    params = {
                    "ID": wu_station_id,
                    "PASSWORD": wu_station_key,
                    "dateutc": "now",
                    "tempf": str(temp_f),
                    "humidity": str(humidity),
                    "baromin": str(pressure),
                    "action": "updateraw"
                    }

                    response = requests.get(upload_url, params=params)

                    logger.info("Status code: %s", response.status_code)
                    logger.info("Response body: %s", response.text)

                except:
                    logger.info("Exception: %s", sys.exc_info()[0])
                    display_red_cross()
                

                # Tick for upload success.
                logger.info("Weather Underground upload success")
                display_green_tick()
                
            else:
                logger.info("Skipping Weather Underground upload")                
                
        # wait some seconds then check again
        # You can always increase the sleep value below to check less often
        time.sleep(1)  
    logger.info("Leaving main()") # this should never happen since the above is an infinite loop

'''*****************************************************************************************************************
   Read Weather Underground Configuration Parameters

*****************************************************************************************************************'''

logger.info("Initializing Weather Underground configuration")
wu_station_id = Config.STATION_ID
wu_station_key = Config.STATION_KEY
wu_screen_rotation = Config.SCREEN_ROTATION
wu_weather_upload = Config.WEATHER_UPLOAD

# we made it this far, so it must have worked...
logger.info("Successfully read configuration values")
logger.info("Station ID: %s", wu_station_id)
logger.info("Screen Rotation: %d", wu_screen_rotation)
logger.info("Weather Upload : %d", wu_weather_upload)

'''*****************************************************************************************************************
   Initialize the Sense HAT object

*****************************************************************************************************************'''
try:
    logger.info("Initializing the Sense HAT")
    sense = SenseHat()
    sense.set_rotation(wu_screen_rotation)

    versionStr = f"V:{__version__}"
    sense.show_message(versionStr, text_colour=[55 + BRIGHTNESS, 55 + BRIGHTNESS, 0], back_colour=[0, 0, 55 + BRIGHTNESS])
    logger.info(versionStr)
   
    sense.clear()
    # get the current temp to use when checking the previous measurement
    last_temp = round(c_to_f(get_temp()), 1)
    logger.info("Current temperature reading: %s", last_temp)
   
except:
    logger.error("Unable to initialize the Sense HAT library: %s", sys.exc_info()[0])
    sys.exit(1)

logger.info("Initialization complete!")

# Now see what we're supposed to do next
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Exiting application")
sys.exit(0)