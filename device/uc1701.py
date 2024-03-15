# MicroPython UC1701 LCD driver, SPI interfaces

from micropython import const
import machine
import framebuf

import asyncio

# register definitions

SET_COLUMN_ADDRESS_LSB = const(0x00)
SET_COLUMN_ADDRESS_MSB = const(0x10)
SET_POWER_CONTROL = const(0x28) # 0b0010 1###
SET_SCROLL_LINE = const(0x40) # 0b01## ####
SET_PAGE_ADDRESS = const(0xB0)
SET_VLCD_RESISTOR_RATIO = const(0x20) # 0b0010 0###
SET_ELECTRONIC_VOLUME_CMD = const(0x81) # Set Contrast
SET_ELECTRONIC_VOLUME_VALUE = const(0x00) # 0b00## ####
SET_ALL_PIXEL_ON = const(0xA4)
SET_INVERSE_DISPLAY = const(0xA6) # 0b1010 011#
SET_DISPLAY_ENABLE = const(0xAE) # 0b1010 111#
SET_SEG_DIRECTION = const(0xA0) # 0b1010 000#
SET_COM_DIRECTION = const(0xC0) # 0b1100 #---
SYSTEM_RESET = const(0xE2)
NOP = const(0xE3)
SET_LCD_BIAS_RATIO = const(0xA2)
SET_CURSOR_UPDATE_MODE = const(0xE0)
RESET_CURSOR_UPDATE_MODE = const(0xEE)
SET_STATIC_INDICATOR_OFF = const(0xAC)
SET_STATIC_INDICATOR_ON = const(0xAD)
SET_BOOSTER_RATIO_1 = const(0xF8)
SET_BOOSTER_RATIO_2 = const(0x00)
SET_POWER_SAVE = const(0x00)
SET_ADV_PROGRAM_CONTROL_0_CMD = const(0xFA) # 0b1111 1010
SET_ADV_PROGRAM_CONTROL_0_VALUE = const(0x00)  # 0b#0## 00##


class _NullPin(machine.Pin):
    def __init__(self, *argv, **kwargs) -> None:
        pass

    def init(self, *argv, **kwargs) -> None:
        pass


_NULL_PIN = _NullPin()


# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class UC1701(framebuf.FrameBuffer):
    def __init__(self, *, br: int = 0b0, pc: int = 0b100, rst: machine.Pin = _NULL_PIN):
        self.width = 128
        self.height = 64
        self.buffer = bytearray(64 * 132 // 8)
        self.rst = rst
        self._br = br
        self._pc = pc
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)

    async def write_cmd(self, cmd: int):
        raise NotImplementedError

    async def write_data(self, data: bytes):
        raise NotImplementedError

    async def power_up(self):
        await self.power_down()
        await self.set_x_mirror(False)
        await self.set_y_mirror(False)
        await self.write_cmd(SET_VLCD_RESISTOR_RATIO | (0b111 & self._pc))
        await self.write_cmd(SET_LCD_BIAS_RATIO | (0b1 & self._br))
        await self.write_cmd(SET_POWER_CONTROL | 0b111)
        await self.wake_up()

    async def power_down(self):
        await self.write_cmd(SYSTEM_RESET)
        await asyncio.sleep(0.005)
        self.rst(0)
        await asyncio.sleep(0.001)
        self.rst(1)
        await asyncio.sleep(0.005)

    async def sleep(self):
        await self.write_cmd(SET_DISPLAY_ENABLE | 0x0)
        await self.write_cmd(SET_ALL_PIXEL_ON | 0x1)

    async def wake_up(self):
        await self.write_cmd(SET_ALL_PIXEL_ON | 0x0)
        await self.write_cmd(SET_DISPLAY_ENABLE | 0x1)

    async def show(self):
        for page in range(8):
            await self.write_cmd(SET_PAGE_ADDRESS | (0xF & page))
            await self.write_cmd(SET_COLUMN_ADDRESS_MSB | 0x0)
            await self.write_cmd(SET_COLUMN_ADDRESS_LSB | 0x0)
            start = self.width * page
            end = start + self.width
            await self.write_data(self.buffer[start:end + 1])

    async def set_x_mirror(self, value: bool):
        await self.write_cmd(SET_SEG_DIRECTION | (0b1 & value))

    async def set_y_mirror(self, value: bool):
        await self.write_cmd(SET_COM_DIRECTION | ((0b1 & value) << 3))

    async def set_inverse(self, value: bool):
        await self.write_cmd(SET_INVERSE_DISPLAY | (0b1 & value))

    async def set_advance_program(self, tr: bool, fr: int, wa: int):
        await self.write_cmd(SET_ADV_PROGRAM_CONTROL_0_CMD)
        await self.write_cmd(
            SET_ADV_PROGRAM_CONTROL_0_VALUE |
            ((0b1 & tr) << 7) |
            ((0b11 & fr) << 4) |
            ((0b11 & wa) << 0)
        )

    async def set_contrast(self, level: int | float | None = None, *, pm: int | None = None):
        if level is None and pm is None:
            raise ValueError("One of value or pm should be specified")
        if level is not None:
            if isinstance(level, int):
                level = level / 255
            pm = int(level * 0b111111)
        assert pm is not None
        await self.write_cmd(SET_ELECTRONIC_VOLUME_CMD)
        await self.write_cmd(SET_ELECTRONIC_VOLUME_VALUE | (0b111111 & pm))

class UC1701_SPI(UC1701):
    def __init__(self, *, spi: machine.SPI, cd: machine.Pin, cs0: machine.Pin = _NULL_PIN, **kwargs):
        self.rate = 10 * 1024 * 1024
        self.spi = spi
        self.dc = cd
        self.dc.init(machine.Pin.OUT, value=0)
        self.cs = cs0
        self.cs.init(machine.Pin.OUT, value=0)
        super().__init__(**kwargs)

    async def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)  # type: ignore
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    async def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)  # type: ignore
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
