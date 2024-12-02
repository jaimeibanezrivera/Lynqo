import RPi.GPIO as GPIO
from hx711 import HX711

# Define GPIO pins
DT = 5  # Data pin
SCK = 6  # Clock pin

def setup():
    GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
    hx = HX711(DT, SCK)
    hx.set_reading_format("MSB", "MSB")  # Bit order
    hx.set_reference_unit(1)  # Reference unit (calibrate later)
    hx.reset()
    hx.tare()  # Reset the scale to 0
    return hx

def loop(hx):
    try:
        while True:
            weight = hx.get_weight(5)  # Average of 5 readings
            print("Weight: {:.2f} grams".format(weight))
            hx.power_down()
            hx.power_up()
    except KeyboardInterrupt:
        print("Exiting...")

def clean_and_exit():
    GPIO.cleanup()

if __name__ == "__main__":
    hx = setup()
    try:
        loop(hx)
    finally:
        clean_and_exit()
