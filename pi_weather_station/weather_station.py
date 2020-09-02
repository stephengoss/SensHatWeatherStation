#!/usr/bin/python
'''*****************************************************************************************************************
    Pi Temperature Station
    Bassed on code orignaly By John M. Wargo www.johnwargo.com

    This is a Raspberry Pi project that measures weather values (temperature, humidity and pressure) using
    the Astro Pi Sense HAT then uploads the data to a Weather Underground weather station.
********************************************************************************************************************'''

from __future__ import print_function
import datetime
import os
import sys
import time
from urllib import urlencode
import urllib2
from sense_hat import SenseHat
from config import Config

# ============================================================================
# Constants
# ============================================================================
# specifies how often to measure values from the Sense HAT (in minutes)
MEASUREMENT_INTERVAL = 2  # (default 10) minutes
SYMBOL_SLEEP = 4          #
# Set to False when testing the code and/or hardware
# Set to True to enable upload of weather data to Weather Underground
WEATHER_UPLOAD = True
UPDATE_ARROW_MINUTE = False
# the weather underground URL used to upload weather data
WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
# some string constants
SINGLE_HASH = "#"
HASHES = "########################################"
SLASH_N = "\n"
BRIGHTNESS = 200

# constants used to display an up and down arrows plus bars
# modified from https://www.raspberrypi.org/learning/getting-started-with-the-sense-hat/worksheet/
# set up the colours (blue, red, empty)
b = [0, 0, 55+BRIGHTNESS]  # blue
r = [55+BRIGHTNESS, 0, 0]  # red
e = [0, 0, 0]   # empty

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
    b, b, b, b, b, b, b, b,
    b, b, b, b, b, b, b, b,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
]
upload = [
    e, r, r, e, e, r, r, e,
    e, r, r, e, e, r, r, e,
    e, r, r, e, e, r, r, e,
    e, r, r, e, e, r, r, e,
    e, r, r, e, e, r, r, e,
    e, r, r, e, e, r, r, e,
    e, r, r, e, e, r, r, e,
    e, e, r, r, r, r, e, e,
]

# ============================================================================
# Functions
# ============================================================================

def print_orientation():
    print("\nprint_orientation")
    north = sense.get_compass()
    print("North: %s" % north)
    print(sense.compass)
    orientation = sense.get_orientation()
    print("p: {pitch}, r: {roll}, y: {yaw}".format(**orientation))
    print(sense.orientation)

    return True

def set_low_light():
    print("\nset_low_light")
    named_tuple = time.localtime()
    time_string = time.strftime("%H:%M", named_tuple)

    if time_string > "7:00" or time_string < "18:00":
        sense.low_light = False
        print("low_light = False")
    else:
        sense.low_light = True
        print("low_light = True")
    
    return True

def set_gamma():
    print("\nset_gamma")
    sense.gamma_reset()
    print('Gamma : ')
    print(sense.gamma)
    sense.clear(255, 127, 0)
    
    return True

def set_brightness():
    print("\nset_brightness")
    named_tuple = time.localtime()
    time_string = time.strftime("%H:%M", named_tuple)

    if time_string > "7:00" or time_string < "18:00":
        print("day brightness = 200")
        BRIGHTNESS = 200
    else:
        BRIGHTNESS = 20
        print("evening brightness = 20")

    return True

def display_red_arrow():
    print("\nDISPLAY_RED_ARROW")
    sense.set_pixels(arrow_up)
    time.sleep(SYMBOL_SLEEP)
    return True

def display_blue_arrow():
    print("\nDISPLAY_BLUE_ARROW")
    sense.set_pixels(arrow_down)
    time.sleep(SYMBOL_SLEEP)
    return True

def display_bars():
    print("\nDISPLAY_BARS")
    sense.set_pixels(bars)
    time.sleep(SYMBOL_SLEEP)
    return True

def display_upload_sign():
    print("\nDISPLAY_UPLOAD_SIGN")
    sense.set_pixels(upload)
    time.sleep(SYMBOL_SLEEP)
    return True

def c_to_f(input_temp):
    # convert input_temp from Celsius to Fahrenheit
    return (input_temp * 1.8) + 32

def get_cpu_temp():
    # 'borrowed' from https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
    # executes a command at the OS to pull in the CPU temperature
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=", "").replace("'C\n", ""))

# use moving average to smooth readings
def get_smooth(x):
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
    return xs

def get_temp():
    # ====================================================================
    # Unfortunately, getting an accurate temperature reading from the
    # Sense HAT is improbable, see here:
    # https://www.raspberrypi.org/forums/viewtopic.php?f=104&t=111457
    # so we'll have to do some approximation of the actual temp
    # taking CPU temp into account. The Pi foundation recommended
    # using the following:
    # http://yaab-arduino.blogspot.co.uk/2016/08/accurate-temperature-reading-sensehat.html
    # ====================================================================
    # First, get temp readings from both sensors
    t1 = sense.get_temperature_from_humidity()
    t2 = sense.get_temperature_from_pressure()
    # t becomes the average of the temperatures from both sensors
    t = (t1 + t2) / 2
    # Now, grab the CPU temperature
    t_cpu = get_cpu_temp()
    # Calculate the 'real' temperature compensating for CPU heating
    t_corr = t - ((t_cpu - t) / 1.5)
    # Finally, average out that value across the last three readings
    t_corr = get_smooth(t_corr)
    # convoluted, right?
    # Return the calculated temperature
    return t_corr

def main():
    global last_temp
    global current_minute
    allIsGood = True
    displaySymbol = True
    displayText = False

    # initialize the lastMinute variable to the current time to start
    last_minute = datetime.datetime.now().minute
    # on startup, just use the previous minute as lastMinute
    last_minute -= 1
    if last_minute == 0:
        last_minute = 59

    last_temp_c = 0

    print_orientation()
    set_gamma()
    set_brightness()
    set_low_light()

    # infinite loop to continuously check weather values
    while allIsGood:
        current_second = datetime.datetime.now().second

        if ((current_second == 0) or ((current_second % 5) == 0)):
            print("Second:%s" % (current_second))
            displaySymbol = not displaySymbol
            displayText = not displayText

            calc_temp = get_temp()
            temp_c = round(calc_temp, 1)
            temp_f = round(c_to_f(calc_temp), 1)
            humidity = round(sense.get_humidity(), 0)
            pressure = round(sense.get_pressure() * 0.0295300, 1)

            print("Temp: %sc, Pressure: %s inHg, Humidity: %s%% Second:%s" % (temp_c, pressure, humidity, current_second))
            print("displayText: %s, displaySymbol: %s" % (str(displayText), str(displaySymbol)))

            if displayText:
                sense.clear()
                sense.show_message(" " + str(temp_c) + "c ", text_colour=[55+BRIGHTNESS, 55+BRIGHTNESS, 0], back_colour=[0, 0, 0])

            if displaySymbol:
                if last_temp_c != temp_c:
                    if last_temp_c > temp_c:
                        # display_blue_arrow
                        print("DOWN")
                        sense.clear()
                        sense.set_pixels(arrow_down)
                    else:
                        # display_red_arrow
                        print("UP")
                        sense.clear()
                        sense.set_pixels(arrow_up)
                else:
                    # display_bars
                    print("STASIS")
                    sense.clear()
                    sense.set_pixels(bars)

            # set last_temp to the current temperature before we measure again
            last_temp_c = temp_c

            # get the current minute
            # current_minute = datetime.datetime.now().minute
            # is it the same minute as the last time we checked?
            # if current_minute != last_minute:
            #     last_minute = current_minute
            #    if (current_minute == 0) or ((current_minute % MEASUREMENT_INTERVAL) == 0):
            if WEATHER_UPLOAD:

                # set the brighness bassed on the time of day.
                set_brightness()
                set_low_light()

                now = datetime.datetime.now()
                # print("\n%d minute mark (%d @ %s)" % (MEASUREMENT_INTERVAL, current_minute, str(now)))
                last_temp = temp_f

                # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
                print("Uploading data to Weather Underground")
                # build a weather data object
                weather_data = {
                    "action": "updateraw",
                    "ID": wu_station_id,
                    "PASSWORD": wu_station_key,
                    "dateutc": "now",
                    "tempf": str(temp_f),
                    "humidity": str(humidity),
                    "baromin": str(pressure),
                }
                try:
                    upload_url = WU_URL + "?" + urlencode(weather_data)
                    response = urllib2.urlopen(upload_url)
                    html = response.read()
                    print("Server response:", html)
                    # do something
                    response.close()  # best practice to close the file
                except:
                    print("Exception:", sys.exc_info()[0], SLASH_N)
            else:
                print("Skipping Weather Underground upload")

    # wait a second then check again
    # You can always increase the sleep value below to check less often
        time.sleep(1)  # this should never happen since the above is an infinite loop

    print("Leaving main()")

# ============================================================================
# here's where we start doing stuff
# ============================================================================
print(SLASH_N + HASHES)
print(SINGLE_HASH, "Julians Pi Weather Station (Stephen Goss)                 ", SINGLE_HASH)
print(SINGLE_HASH, "Bassed on code originaly written by John M. Wargo (www.johnwargo.com)", SINGLE_HASH)
print(HASHES)

# make sure we don't have a MEASUREMENT_INTERVAL > 60
if (MEASUREMENT_INTERVAL is None) or (MEASUREMENT_INTERVAL > 60):
    print("The application's 'MEASUREMENT_INTERVAL' cannot be empty or greater than 60")
    sys.exit(1)

# ============================================================================
#  Read Weather Underground Configuration Parameters
# ============================================================================
print("\nInitializing Weather Underground configuration")
wu_station_id = Config.STATION_ID
wu_station_key = Config.STATION_KEY
if (wu_station_id is None) or (wu_station_key is None):
    print("Missing values from the Weather Underground configuration file\n")
    sys.exit(1)

# we made it this far, so it must have worked...
print("Successfully read Weather Underground configuration values")
print("Station ID:", wu_station_id)
# print("Station key:", wu_station_key)

# ============================================================================
# initialize the Sense HAT object
# ============================================================================
try:
    print("Initializing the Sense HAT client")
    sense = SenseHat()
    # sense.set_rotation(180)
    # then write some text to the Sense HAT's 'screen'
    sense.show_message("Julians WS", text_colour=[55+BRIGHTNESS, 55+BRIGHTNESS, 0], back_colour=[0, 0, 55+BRIGHTNESS])

    # clear the screen
    sense.clear()
    # get the current temp to use when checking the previous measurement
    last_temp = round(c_to_f(get_temp()), 1)
    print("Current temperature reading:", last_temp)
except:
    print("Unable to initialize the Sense HAT library:", sys.exc_info()[0])
    sys.exit(1)

print("Initialization complete!")

# Now see what we're supposed to do next
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting application\n")
        sys.exit(0)
