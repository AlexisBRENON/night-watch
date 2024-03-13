# MicroPython UC1701 LCD driver, I2C and SPI interfaces

from micropython import const
import machine
import framebuf

import asyncio

# register definitions

SET_COLUMN_ADDRESS_LSB = const(0x00)
SET_COLUMN_ADDRESS_MSB = const(0x10)
SET_POWER_CONTROL = const(0x28)
SET_SCROLL_LINE = const(0x40)
SET_PAGE_ADDRESS = const(0xB0)
SET_VLCD_RESISTOR_RATIO = const(0x20)
SET_ELECTRONIC_VOLUME_CMD = const(0x81)
SET_ELECTRONIC_VOLUME_VALUE = const(0x20)
SET_ALL_PIXEL_ON = const(0xA4)
SET_INVERSE_DISPLAY = const(0xA6)
SET_DISPLAY_ENABLE = const(0xAE)
SET_SEG_DIRECTION = const(0xA0)
SET_COM_DIRECTION = const(0xC0)
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
SET_ADV_PROGRAM_CONTROL_0_1 = const(0xFA)
SET_ADV_PROGRAM_CONTROL_0_2 = const(0x90)

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class UC1701(framebuf.FrameBuffer):
    def __init__(self):
        self.width = 128
        self.height = 64
        self.buffer = bytearray(64 * 132 // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB, 132)

    def write_cmd(self, cmd: int):
        raise NotImplementedError

    def write_data(self, data: bytes):
        raise NotImplementedError

    async def power_up(self):
        for cmd in (
            SET_SEG_DIRECTION | 0x1,
            SET_COM_DIRECTION | 0x0,
            SET_VLCD_RESISTOR_RATIO | 0x3,
            SET_LCD_BIAS_RATIO | 0x0,
            SET_ELECTRONIC_VOLUME_CMD,
            SET_ELECTRONIC_VOLUME_VALUE | 0x8,
        ):
            self.write_cmd(cmd)
        await self.show()
        self.write_cmd(SET_POWER_CONTROL | 0x1)
        self.write_cmd(SET_DISPLAY_ENABLE | 0x1)

    async def power_down(self):
        self.write_cmd(SYSTEM_RESET)
        await asyncio.sleep_ms(5)

    async def sleep(self):
        self.write_cmd(SET_DISPLAY_ENABLE | 0x0)
        self.write_cmd(SET_ALL_PIXEL_ON | 0x1)

    async def wake_up(self):
        self.write_cmd(SET_ALL_PIXEL_ON | 0x0)
        self.write_cmd(SET_DISPLAY_ENABLE | 0x1)

    async def invert(self, invert):
        self.write_cmd(SET_INVERSE_DISPLAY | (invert & 0x1))

    async def show(self):
        self.write_cmd(SET_PAGE_ADDRESS | 0x0)
        self.write_cmd(SET_COLUMN_ADDRESS_MSB | 0x0)
        self.write_cmd(SET_COLUMN_ADDRESS_LSB | 0x0)
        self.write_data(self.buffer)

class UC1701_SPI(UC1701):
    def __init__(self, spi: machine.SPI, cd: machine.Pin, rst: machine.Pin | None = None, cs0: machine.Pin | None = None):
        self.rate = 10 * 1024 * 1024
        self.spi = spi
        self.dc = cd
        self.dc.init(machine.Pin.OUT, value=0)

        if rst is not None:
            rst.init(machine.Pin.OUT, value=0)
        self.res = rst or (lambda x: x)

        if cs0 is not None:
            cs0.init(machine.Pin.OUT, value=1)
        self.cs = cs0 or (lambda x: x)
        super().__init__()

    async def power_up(self):
        self.res(1)
        await asyncio.sleep_ms(1)
        self.res(0)
        await asyncio.sleep_ms(1)
        self.res(1)
        await asyncio.sleep_ms(5)

        return await super().power_up()

    async def power_down(self):
        await super().power_down()
        self.res(0)
        await asyncio.sleep_ms(1)
        self.res(1)
        await asyncio.sleep_ms(5)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
