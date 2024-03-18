import machine
import asyncio
import time

import micropython


class Click:
    NONE = micropython.const("")
    SHORT = micropython.const(".")
    LONG = micropython.const("_")

    def __init__(
        self,
        pin: machine.Pin,
        timer: machine.Timer | None = None,
        bounce_time: int = 25,
        trigger: int = machine.Pin.IRQ_FALLING,
    ):
        self._signal = machine.Signal(pin, trigger == machine.Pin.IRQ_RISING)
        self._timer = timer or machine.Timer(-1)
        self._bounce = bounce_time
        self._debounce_start = time.ticks_ms()
        self._debounce_end = time.ticks_ms()
        self._signal.irq(self._on_press, machine.Signal.IRQ_FALLING)
        self._signal.irq(self._on_release, machine.Signal.IRQ_RISING)

        self.is_pressed = asyncio.Event()
        self.is_long = asyncio.Event()
        self._set_is_long_cb = self.is_long.set
        self.is_released = asyncio.Event()

        self._events = [self.NONE] * 5
        self._event_count = 0

    @property
    def events(self) -> tuple[str]:
        return tuple(self._events[0 : self._event_count])

    def _on_press(self, pin: machine.Pin):
        self._debounce_end = time.ticks_ms()
        if time.ticks_diff(self._debounce_end, self._debounce_start) > self._bounce:
            self._debounce_start = self._debounce_end

            self.is_released.clear()
            self.is_pressed.set()
            self._timer.init(
                mode=self._timer.ONE_SHOT,
                period=3 * self._bounce,
                callback=self.is_long.set,
            )

    def _on_release(self, pin: machine.Pin):
        self._debounce_end = time.ticks_ms()
        if time.ticks_diff(self._debounce_end, self._debounce_start) > self._bounce:
            self._debounce_start = self._debounce_end

            self._timer.deinit()
            if self.is_pressed.is_set():
                if self.is_long.is_set():
                    self._events[self._event_count] = self.LONG
                else:
                    self._events[self._event_count] = self.SHORT
                self.is_long.clear()
            self.is_pressed.clear()
            self._event_count += 1

            self.is_released.set()
            self._timer.init(
                mode=self._timer.ONE_SHOT,
                period=7 * self._bounce,
                callback=self._on_event_end,
            )

    def _on_event_end(self, timer: machine.Timer):
        self._timer.deinit()
        self.is_pressed.clear()
        self.is_released.clear()
        self.is_long.clear()
        self._events[:] = self.NONE
        self._event_count = 0
