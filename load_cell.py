import time
import sys
import lgpio


class HX711:
    def __init__(self, data_pin, clock_pin, gpio_chip=0):
        self.data_pin = data_pin
        self.clock_pin = clock_pin
        self.gpio_chip = gpio_chip
        self.offset = 0
        self.reference_unit = 1
        self.byte_format = "MSB"  # Default byte order
        self.bit_format = "MSB"  # Default bit order

        # Open GPIO chip
        self.handle = lgpio.gpiochip_open(self.gpio_chip)

        # Set up pins
        lgpio.gpio_claim_input(self.handle, self.data_pin)
        lgpio.gpio_claim_output(self.handle, self.clock_pin)
        lgpio.gpio_write(self.handle, self.clock_pin, 0)  # Set clock pin low

    def set_reading_format(self, byte_format, bit_format):
        """
        Set the byte and bit order. Supported values are MSB or LSB.
        """
        if byte_format not in ["MSB", "LSB"] or bit_format not in ["MSB", "LSB"]:
            raise ValueError("Byte and Bit format must be either 'MSB' or 'LSB'.")
        self.byte_format = byte_format
        self.bit_format = bit_format
        print(f"Set reading format: Byte={self.byte_format}, Bit={self.bit_format}")

    def read(self):
        """
        Read raw 24-bit data from the HX711, applying byte and bit order.
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

        # Apply byte order (reverse bits if LSB)
        if self.byte_format == "LSB":
            count = int('{:024b}'.format(count)[::-1], 2)

        # Convert from two's complement
        if count & 0x800000:
            count -= 0x1000000

        return count

    def set_reference_unit(self, reference_unit):
        """
        Set the reference unit for converting raw data to weight.
        """
        self.reference_unit = reference_unit

    def tare(self):
        """
        Tare the scale (zero out the offset).
        """
        print("Taring... Ensure the scale is empty.")
        time.sleep(1)
        self.offset = sum([self.read() for _ in range(10)]) / 10
        print(f"Tare complete. Offset: {self.offset}")

    def get_weight(self, times=5):
        """
        Get the weight after applying offset and reference unit.
        """
        readings = [self.read() for _ in range(times)]
        raw_value = sum(readings) / len(readings)
        weight = (raw_value - self.offset) / self.reference_unit
        return weight

    def power_down(self):
        """
        Power down the HX711.
        """
        lgpio.gpio_write(self.handle, self.clock_pin, 1)
        time.sleep(0.0001)

    def power_up(self):
        """
        Power up the HX711.
        """
        lgpio.gpio_write(self.handle, self.clock_pin, 0)
        time.sleep(0.0001)

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
    sys.exit()


if __name__ == "__main__":
    hx = HX711(data_pin=5, clock_pin=6)

    # Set reading format to LSB, MSB
    hx.set_reading_format("LSB", "MSB")

    # Set reference unit and tare
    hx.set_reference_unit(114)  # Adjust this after calibration
    hx.tare()

    print("Tare done! Add weight now...")

    try:
        while True:
            weight = hx.get_weight(5)
            print(f"Weight: {weight:.2f} g")
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        clean_and_exit(hx)
