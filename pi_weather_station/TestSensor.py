import os
import glob

def list_w1_devices():
    base_dir = '/sys/bus/w1/devices/'
    
    try:
        devices = os.listdir(base_dir)
        print("Devices in /sys/bus/w1/devices/:")
        for device in devices:
            print(f" - {device}")
    except FileNotFoundError:
        print("Directory /sys/bus/w1/devices/ not found. Is 1-Wire enabled?")

# Run listing


def detect_ds18b20():
    # Path to 1-Wire devices
    base_dir = '/sys/bus/w1/devices/'
    
    # Find all directories starting with '28-' (DS18B20 sensors have IDs like 28-xxxx)
    device_folders = glob.glob(base_dir + '28-*')

    if device_folders:
        print("DS18B20 sensor detected:")
        for device in device_folders:
            print(f" - {device}")
        return True
    else:
        print("No DS18B20 sensor detected.  no /sys/bus/w1/devices/28-* directores")
        return False

# Run detection
list_w1_devices()
detect_ds18b20()