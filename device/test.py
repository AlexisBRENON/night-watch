import asyncio

import click
import c3pico

click_handler = click.Click(c3pico.button)

i = 0
c3pico.rgb_led(i, i, i)
while True:
    print("Waiting for press...")
    asyncio.run(click_handler.is_pressed.wait())
    print("Passed events: ", click_handler.events)
    i = 10 * (len(click_handler.events) + 1)
    c3pico.rgb_led(i, i, i)
    print("Waiting for release...")
    asyncio.run(click_handler.is_released.wait())
    print("Registered events: ", click_handler.events)
    if click_handler.events == (
        click_handler.LONG,
        click_handler.LONG,
        click_handler.LONG,
    ):
        c3pico.rgb_led(i, 0, 0)
        break

print("Done")
