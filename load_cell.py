import time
import lgpio

class HX711:
    def __init__(self, data_pin, clock_pin, gpio_chip=0):
        self.data_pin = data_pin
        self.clock_pin = clock_pin
        self.gpio_chip = gpio_chip

        # Open GPIO chip
        self.handle = lgpio.gpiochip_open(self.gpio_chip)

        # Set up pins
        lgpio.gpio_claim_input(self.handle, self.data_pin)
        lgpio.gpio_claim_output(self.handle, self.clock_pin)
        lgpio.gpio_write(self.handle, self.clock_pin, 0)  # Set clock pin low

    def tare(self):
        print("Taring... Make sure there is no weight on the load cell.")
        time.sleep(1)  # Allow system to stabilize before taring
        raw_tare_value = self.read()
        print(f"Tare value: {raw_tare_value}")
        return raw_tare_value

    def read(self):
        count = 0

        # Wait until the data line goes low (ready)
        while lgpio.gpio_read(self.handle, self.data_pin) == 1:
            pass

        # Read 24 bits of data from the HX711
        for _ in range(24):
            lgpio.gpio_write(self.handle, self.clock_pin, 1)
            count = count << 1
            if lgpio.gpio_read(self.handle, self.data_pin):
                count += 1
            lgpio.gpio_write(self.handle, self.clock_pin, 0)

        # Set the clock pin high for one extra bit to signal end of reading
        lgpio.gpio_write(self.handle, self.clock_pin, 1)
        lgpio.gpio_write(self.handle, self.clock_pin, 0)

        # Convert 2's complement if needed
        if count & 0x800000:
            count -= 0x1000000

        return count

    def cleanup(self):
        # Release GPIO pins and close the chip
        lgpio.gpiochip_close(self.handle)

def setup():
    data_pin = 5  # GPIO pin connected to HX711 DT (Data)
    clock_pin = 6  # GPIO pin connected to HX711 SCK (Clock)
    hx = HX711(data_pin, clock_pin)

    # Tare the load cell and wait for stabilization
    tare_value = hx.tare()
    print("Tare completed.")
    time.sleep(2)  # Wait 2 seconds to stabilize after taring
    return hx

def loop(hx):
    try:
        while True:
            weight = hx.read()
            print(f"Raw Weight: {weight}")
            time.sleep(0.5)  # Adjust delay based on reading frequency
    except KeyboardInterrupt:
        print("Exiting...")

def clean_and_exit(hx):
    hx.cleanup()
    print("GPIO cleaned up.")

if __name__ == "__main__":
    hx = setup()
    try:
        loop(hx)
    finally:
        clean_and_exit(hx)
