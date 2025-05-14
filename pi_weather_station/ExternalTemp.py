import glob
import time

def read_temp_raw():
    base_dir = '/sys/bus/w1/devices/'
    
    device_folder = glob.glob(base_dir + '28*')[0]  # '28*' is the DS18B20 family code
    device_file = device_folder + '/w1_slave'
    with open(device_file, 'r') as f:
        return f.readlines()

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

print(f"Temperature: {read_temp():.2f} °C")
