import asyncio
import time

import ntptime

import wlan

import c3pico
import click

click_handler = click.Click(c3pico.button)


async def test_click():
    i = 0
    c3pico.rgb_led(i, i, i)
    print(click_handler)
    while True:
        print("Waiting for press...", click_handler)
        await click_handler.is_pressed.wait()
        i = 10 * (len(click_handler.events) + 1)
        c3pico.rgb_led(i, i, i)
        print("Waiting for release...", click_handler)
        await click_handler.is_released.wait()
        if click_handler.events == (
            click_handler.LONG,
            click_handler.LONG,
            click_handler.LONG,
        ):
            c3pico.rgb_led(i, 0, 0)
            break
        print("Continue...")

    print("Done")


async def test_ntp():
    print("UTC time before synchronization: %s" % str(time.gmtime()))
    net_connection = await wlan.get_instance()
    print(net_connection.config("ssid"))
    if net_connection.config("ssid") != wlan.AP_SSID:
        ntptime.settime(timezone=0, server="fr.pool.ntp.org")
        print("UTC time after synchronization: %s" % str(time.gmtime()))


if __name__ == "__main__":
    asyncio.run(test_click())
