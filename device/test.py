import asyncio
import time

import ntptime

import wlan

import c3pico
import click

click_handler = click.Click(c3pico.button)

colors = (
    (50, 0, 0),  # Red
    (50, 10, 0),  # Orange
    (50, 20, 0),  # Yellow
    (20, 40, 0),  # Green
    (0, 30, 30),  # Cyan
    (0, 0, 50),  # Blue
    (50, 0, 30),  # Purple
)


async def test_click():
    i = 0
    c3pico.rgb_led(0, 0, 0)
    while True:
        print("Waiting for press...", click_handler)
        await click_handler.is_pressed.wait()
        i = (i + 1) % len(colors)
        c3pico.rgb_led(*colors[i])
        print("Waiting for release...", click_handler)
        await click_handler.is_released.wait()
        if click_handler.clicks == (
            click_handler.LONG,
            click_handler.LONG,
            click_handler.LONG,
        ):
            c3pico.rgb_led(100, 100, 100)
            break
        print("Continue...")

    print("Done")


async def test_ntp():
    print("UTC time before synchronization: %s" % str(time.gmtime()))
    net_connection = await wlan.get_instance()
    print("SSID:", net_connection.config("ssid"))
    if net_connection.config("ssid") != wlan.AP_SSID:
        ntptime.settime()
        print("UTC time after synchronization: %s" % str(time.gmtime()))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_ntp())
