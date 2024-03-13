import c3pico
import time


i = 0
mul = 0
while True:
    c3pico.rgb_led(*tuple(128 if n == i else 0 for n in range(3)))
    time.sleep(0.4)
    i = (i + 1) % 3
