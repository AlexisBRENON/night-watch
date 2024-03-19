import machine
import asyncio
import time

import micropython


class Click:
    _PRESS = micropython.const((True, False, False))
    _LONGPRESS = micropython.const((True, True, False))
    _RELEASE = micropython.const((False, False, True))
    _NONE = micropython.const((False, False, False))
    _STOPPED = micropython.const((True, True, True))

    _EVENT = micropython.const("?")
    SHORT = micropython.const(".")
    LONG = micropython.const("_")

    def __init__(
        self,
        pin: machine.Pin,
        timer: machine.Timer = machine.Timer(0),
        long_ms: int = 500,
        invert: bool = False,
    ):
        self._pin = pin
        self._timer = timer
        self._long_ms = long_ms
        self._short_ms = long_ms // 3
        self._bounce = self._short_ms // 5
        self._invert = invert

        self._debounce_start = time.ticks_ms()
        self._debounce_end = time.ticks_ms()

        self._update_state = asyncio.ThreadSafeFlag()

        self.is_pressed = asyncio.Event()
        self.is_long = asyncio.Event()
        self.is_released = asyncio.Event()
        self._events = (self.is_pressed, self.is_long, self.is_released)

        self._state = self._NONE
        self._clicks = []

        self._pin.irq(self._debounce, machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING)

    async def handle(self):
        while self._state is not self._STOPPED:
            print(self)
            try:
                await asyncio.wait_for(self._update_state.wait(), 1000)
            except TimeoutError:
                continue

            for state, event in zip(self._state, self._events):
                event.set() if state else event.clear()

    def stop(self):
        self._state = self._STOPPED

    @property
    def clicks(self) -> tuple[str]:
        return tuple(self._clicks)

    def _debounce(self, pin: machine.Pin):
        self._debounce_end = time.ticks_ms()
        if time.ticks_diff(self._debounce_end, self._debounce_start) > self._bounce:
            if pin.value() == self._invert:
                micropython.schedule(Click._on_press, self)
            else:
                micropython.schedule(Click._on_release, self)
        self._debounce_start = self._debounce_end

    def _set_is_long_cb(self, _: machine.Timer):
        self._state = self._LONGPRESS
        self._update_state.set()

    def _on_press(self):
        self._timer.deinit()
        self._state = self._PRESS
        self._update_state.set()
        self._timer.init(
            mode=self._timer.ONE_SHOT,
            period=self._long_ms,
            callback=self._set_is_long_cb,
        )

    def _on_release(self):
        self._timer.deinit()
        if self._state in {self._PRESS, self._LONGPRESS}:
            self._clicks.append(
                self.LONG if self._state == self._LONGPRESS else self.SHORT
            )

        self._state = self._RELEASE
        self._update_state.set()
        self._timer.init(
            mode=self._timer.ONE_SHOT,
            period=5 * self._short_ms,
            callback=self._on_event_end,
        )

    def _on_event_end(self, _: machine.Timer):
        self._timer.deinit()
        self._clicks.clear()
        self._state = self._NONE
        self._update_state.set()

    def __str__(self) -> str:
        return f"Click({self._pin}):\n\tpressed (long): {self.is_pressed.is_set()} ({self.is_long.is_set()}),\n\treleased: {self.is_released.is_set()}\n\tevents: {self.clicks}"


if __name__ == "__main__":
    import c3pico

    h = Click(c3pico.button)

    asyncio.run(h.handle())


# import click; import c3pico; import asyncio; h = click.Click(c3pico.button); asyncio.run(h.handle())
