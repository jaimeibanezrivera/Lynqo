import time
import sys
import lgpio

#hx711 library giving problems, so we wrote the important functions here
class HX711:
    def __init__(self, data_pin, clock_pin, gpio_chip=0):
        self.data_pin = data_pin
        self.clock_pin = clock_pin
        self.gpio_chip = gpio_chip
        self.reference_unit = 1
        self.offset = 0

        # Open GPIO chip
        self.handle = lgpio.gpiochip_open(self.gpio_chip)

        # Set up pins
        lgpio.gpio_claim_input(self.handle, self.data_pin)
        lgpio.gpio_claim_output(self.handle, self.clock_pin)
        lgpio.gpio_write(self.handle, self.clock_pin, 0)  # Set clock pin low

    def set_reading_format(self, byte_format, bit_format):
        """
        Set the byte and bit order. For now, we just keep this for compatibility.
        """
        if byte_format != "MSB" or bit_format != "MSB":
            raise NotImplementedError("Only MSB, MSB is currently supported.")

    def set_reference_unit(self, reference_unit):
        """
        Set the reference unit for converting raw data into meaningful weight values.
        """
        self.reference_unit = reference_unit

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

    def tare(self):
        """
        Tare the scale (set the current reading as the zero point).
        """
        print("Taring... Please ensure the load cell is empty.")
        time.sleep(1)
        readings = [self.read() for _ in range(10)]
        self.offset = sum(readings) / len(readings)
        print(f"Tare complete. Offset: {self.offset}")

    def get_weight(self, times=5):
        """
        Get the weight, adjusted by the tare offset and reference unit.
        """
        readings = [self.read() for _ in range(times)]
        raw_value = sum(readings) / len(readings)
        weight = (raw_value - self.offset) / self.reference_unit
        return weight

    def power_down(self):
        """
        Power down the HX711 to save energy.
        """
        lgpio.gpio_write(self.handle, self.clock_pin, 1)
        time.sleep(0.0001)  # Wait for a short time

    def power_up(self):
        """
        Power up the HX711.
        """
        lgpio.gpio_write(self.handle, self.clock_pin, 0)
        time.sleep(0.0001)  # Wait for a short time

    def cleanup(self):
        """
        Clean up GPIO resources.
        """
        lgpio.gpiochip_close(self.handle)


def clean_and_exit(hx):
    """
    Clean up and exit the program.
    """
    print("Cleaning up...")
    hx.cleanup()
    print("Bye!")
    sys.exit()


if __name__ == "__main__":
    # Initialize HX711 with pins 5 (DT) and 6 (SCK)
    hx = HX711(data_pin=5, clock_pin=6)
    hx.set_reading_format("MSB", "MSB")
    hx.set_reference_unit(114)  # Set the reference unit (calibrate this value)
    hx.tare()  # Perform tare

    print("Tare done! Add weight now...")

    try:
        while True:
            # Get weight and print it
            weight = hx.get_weight(5)  # Average over 5 readings
            print(f"Weight: {weight:.2f} g")

            # Power down and up for stability
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        clean_and_exit(hx)
