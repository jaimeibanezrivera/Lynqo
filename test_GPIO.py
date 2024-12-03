import lgpio

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, 18)
lgpio.gpio_write(h, 18, 1)
lgpio.gpiochip_close(h)
print("GPIO test succesfull")
