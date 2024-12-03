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

    def read(self):
        """
        Read raw 24-bit data from the HX711.
        """
        count = 0

        # Wait for the data pin to go low (ready)
        while lgpio.gpio_read(self.handle, self.data_pin) == 1:
            pass

        # Read 24 bits of data
        for _ in range(24):
            lgpio.gpio_write(self.handle, self.clock_pin, 1)
            count = count << 1
            if lgpio.gpio_read(self.handle, self.data_pin):
                count += 1
            lgpio.gpio_write(self.handle, self.clock_pin, 0)

        # Set the clock pin high for one extra bit
        lgpio.gpio_write(self.handle, self.clock_pin, 1)
        lgpio.gpio_write(self.handle, self.clock_pin, 0)

        # Convert from two's complement
        if count & 0x800000:
            count -= 0x1000000

        return count

    def cleanup(self):
        """
        Clean up GPIO resources.
        """
        if self.handle is not None:
            lgpio.gpiochip_close(self.handle)
            self.handle = None


def clean_and_exit(hx):
    """
    Clean up and exit the program.
    """
    print("Cleaning up GPIO...")
    hx.cleanup()
    print("Exiting program.")
    exit()


if __name__ == "__main__":
    # Initialize HX711 with pins 5 (DT) and 6 (SCK)
    hx = HX711(data_pin=5, clock_pin=6)

    print("Reading raw data from HX711. Press Ctrl+C to exit.")

    try:
        while True:
            raw_value = hx.read()
            print(f"Raw value: {raw_value}")
            time.sleep(0.5)  # Adjust the delay as needed for your use case

    except (KeyboardInterrupt, SystemExit):
        clean_and_exit(hx)
