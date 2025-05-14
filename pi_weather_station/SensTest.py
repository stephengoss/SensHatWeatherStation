from sense_hat import SenseHat

# Initialize Sense HAT
sense = SenseHat()

# Read temperature
temperature = sense.get_temperature()

# Print it
print(f"Temperature: {temperature:.2f} °C")
