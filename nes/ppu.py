from __future__ import annotations
import random

from enum import Enum
from typing import Optional, List, Tuple
from pygame import Surface

from .cartridge import Cartridge


class PPU:
    """
    An emulation of the 2C02 picture processing unit.
    """

    __slots__ = ("controller_reg", "mask_reg", "status_reg", "address_reg", "data_reg",
                 "name_table", "pattern_table", "palette_table", "cart", "frame_complete", "screen", "patterns",
                 "_cycles", "_scanline", "_clock_count", "_colors")

    class CONTROLLER(Enum):
        """
        The controller register flags.
        """
        NX  = 1 << 0  # Nametable X
        NY  = 1 << 1  # Nametable Y
        IM  = 1 << 2  # Increment mode
        PS  = 1 << 3  # Pattern sprite
        PB  = 1 << 4  # Pattern background
        SS  = 1 << 5  # Sprite size
        MSS = 1 << 6  # Master/Slave select
        NMI = 1 << 7  # Enable NMI

    class MASK(Enum):
        """
        The mask register flags.
        """
        CGS = 1 << 0  # Grayscale
        RBL = 1 << 1  # Render background in leftmost
        RSL = 1 << 2  # Render sprites in leftmost
        RB  = 1 << 3  # Render background
        RS  = 1 << 4  # Render sprites
        CR  = 1 << 5  # Emphasise red
        CG  = 1 << 6  # Emphasise green
        CB  = 1 << 7  # Emphasise blue

    class STATUS(Enum):
        """
        The status register flags.
        """
        SO = 1 << 5  # Sprite overflow
        SH = 1 << 6  # Sprite 0 hit
        VB = 1 << 7  # Vertical blank

    def __init__(self) -> None:
        # PPU internal registers:
        self.controller_reg: int = 0x00
        self.mask_reg: int = 0x00
        self.status_reg: int = 0x00
        self.address_reg: int = 0x00
        self.data_reg: int = 0x00

        # PPU bus:
        self.name_table: List[List[int]] = 2 * [1024 * [0x00]]
        self.pattern_table: List[List[int]] = 2 * [4096 * [0x00]]
        self.palette_table: List[int] = 32 * [0x00]
        self.cart: Optional[Cartridge] = None

        # For the purpose of emulation:
        self.frame_complete: bool = False
        self.screen: Surface = Surface((341, 261))
        self.patterns: Tuple[Surface, Surface] = (Surface((128, 128)), Surface((128, 128)))

        # Helper variables:
        self._cycles: int = 0
        self._scanline: int = 0
        self._clock_count: int = 0

        self._colors: Tuple[Tuple[int, int, int], ...] = (
            ( 84,  84,  84), (  0,  30, 116), (  8,  16, 144), ( 48,   0, 136),
            ( 68,   0, 100), ( 92,   0,  48), ( 84,   4,   0), ( 60,  24,   0),
            ( 32,  42,   0), (  8,  58,   0), (  0,  64,   0), (  0,  60,   0),
            (  0,  50,  60), (  0,   0,   0), (  0,   0,   0), (  0,   0,   0),

            (152, 150, 152), (  8,  76, 196), ( 48,  50, 236), ( 92,  30, 228),
            (136,  20, 176), (160,  20, 100), (152,  34,  32), (120,  60,   0),
            ( 84,  90,   0), ( 40, 114,   0), (  8, 124,   0), (  0, 118,  40),
            (  0, 102, 120), (  0,   0,   0), (  0,   0,   0), (  0,   0,   0),

            (236, 238, 236), ( 76, 154, 236), (120, 124, 236), (176,  98, 236),
            (228,  84, 236), (236,  88, 180), (236, 106, 100), (212, 136,  32),
            (160, 170,   0), (116, 196,   0), ( 76, 208,  32), ( 56, 204, 108),
            ( 56, 180, 204), ( 60,  60,  60), (  0,   0,   0), (  0,   0,   0),

            (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
            (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
            (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
            (160, 214, 228), (160, 162, 160), (  0,   0,   0), (  0,   0,   0),
        )

    def _get_flag(self, register: str, flag: PPU.CONTROLLER | PPU.MASK | PPU.STATUS) -> bool:
        """
        Returns the state of a specific bit of the requested register.
        """
        return (getattr(self, register) & flag.value) > 0

    def _set_flag(self, register: str, flag: PPU.CONTROLLER | PPU.MASK | PPU.STATUS, value: bool) -> None:
        """
        Sets or resets a specific bit of the requested register.
        """
        setattr(self, register, getattr(self, register) ^ (-value ^ getattr(self, register)) & flag.value)

    def connect_cartridge(self, cart: Cartridge) -> None:
        """
        Connects the cartridge to the PPU bus.
        """
        self.cart = cart

    def reset(self) -> None:
        """
        Forces PPU into known state.
        """
        self.controller_reg = 0x00
        self.mask_reg = 0x00
        self.status_reg = 0x00
        self.address_reg = 0x00
        self.data_reg = 0x00

        self._cycles = 0
        self._scanline = 0

    def clock(self) -> None:
        """
        Performs one clock cycle's worth of update.
        """
        # Produce some noise:
        self.screen.set_at((self._cycles - 1, self._scanline), self._colors[random.choice((0x3F, 0x30))])

        self._clock_count += 1
        self._cycles += 1

        if self._cycles >= 341:
            self._cycles = 0
            self._scanline += 1

            if self._scanline >= 261:
                self._scanline = -1
                self.frame_complete = True

    def write(self, address: int, data: int) -> None:
        """
        Writes a byte to the specified PPU register.
        """
        # PPU controller register:
        if address == 0x0000:
            self.controller_reg = data

        # PPU mask register:
        elif address == 0x0001:
            self.mask_reg = data

        # PPU status register:
        elif address == 0x0002:
            pass

        # OAM address port
        elif address == 0x0003:
            pass

        # OAM data port
        elif address == 0x0004:
            pass

        # PPU scrolling position register:
        elif address == 0x0005:
            pass

        # PPU address register:
        elif address == 0x0006:
            pass

        # PPU data port:
        elif address == 0x0007:
            self._write(self.address_reg, data)
            self.address_reg += 32 if self._get_flag("controller_reg", PPU.CONTROLLER.IM) else 1

    def read(self, address: int, read_only: bool = False) -> int:
        """
        Reads a byte from the specified PPU register.
        """
        # PPU controller register:
        if address == 0x0000 and read_only:
            return self.controller_reg

        # PPU mask register:
        if address == 0x0001 and read_only:
            return self.mask_reg

        # PPU status register:
        if address == 0x0002:
            if read_only:
                return self.status_reg

            temp = (self.status_reg & 0xE0) | (self.data_reg & 0x1F)
            self._set_flag("status_reg", PPU.STATUS.VB, False)
            return temp

        # OAM address port
        if address == 0x0003:
            pass

        # OAM data port
        if address == 0x0004:
            pass

        # PPU scrolling position register:
        if address == 0x0005:
            pass

        # PPU address register:
        if address == 0x0006:
            pass

        # PPU data port:
        if address == 0x0007 and not read_only:
            temp = self.data_reg
            self.data_reg = self._read(self.address_reg)
            if self.address_reg >= 0x3F00:
                temp = self.data_reg
            self.address_reg += 32 if self._get_flag("controller_reg", PPU.CONTROLLER.IM) else 1
            return temp

        return 0x00

    def _write(self, address: int, data: int) -> None:
        """
        Enables writing to the PPU bus.
        """
        address &= 0x3FFF

        if 0x0000 <= address <= 0x1FFF:
            self.pattern_table[(address & 0x1000) >> 12][address & 0x0FFF] = data

        elif 0x2000 <= address <= 0x3EFF and self.cart:
            address &= 0x0FFF
            if self.cart.mirror == Cartridge.MIRROR.HORIZONTAL:
                if 0x0000 <= address <= 0x07FF:
                    self.name_table[0][address & 0x03FF] = data
                elif 0x0800 <= address <= 0x0FFF:
                    self.name_table[1][address & 0x03FF] = data

            elif self.cart.mirror == Cartridge.MIRROR.VERTICAL:
                if 0x0000 <= address <= 0x03FF or 0x0800 <= address <= 0x0BFF:
                    self.name_table[0][address & 0x03FF] = data
                elif 0x0400 <= address <= 0x07FF or 0x0C00 <= address <= 0x0FFF:
                    self.name_table[1][address & 0x03FF] = data

        elif 0x3F00 <= address <= 0x3FFF:
            address &= 0x1F
            if address in (0x10, 0x14, 0x18, 0x1C):
                address &= 0xF
            self.palette_table[address] = data

        elif self.cart:
            self.cart.write(address & 0x3FFF, data)

    def _read(self, address: int, read_only: bool = False) -> int:
        """
        Enables reading from the PPU bus.
        """
        address &= 0x3FFF

        if 0x0000 <= address <= 0x1FFF:
            return self.pattern_table[(address & 0x1000) >> 12][address & 0x0FFF]

        if 0x2000 <= address <= 0x3EFF and self.cart:
            address &= 0x0FFF
            if self.cart.mirror == Cartridge.MIRROR.HORIZONTAL:
                if 0x0000 <= address <= 0x07FF:
                    return self.name_table[0][address & 0x03FF]
                if 0x0800 <= address <= 0x0FFF:
                    return self.name_table[1][address & 0x03FF]

            if self.cart.mirror == Cartridge.MIRROR.VERTICAL:
                if 0x0000 <= address <= 0x03FF or 0x0800 <= address <= 0x0BFF:
                    return self.name_table[0][address & 0x03FF]
                if 0x0400 <= address <= 0x07FF or 0x0C00 <= address <= 0x0FFF:
                    return self.name_table[1][address & 0x03FF]

        if 0x3F00 <= address <= 0x3FFF:
            address &= 0x1F
            if address in (0x10, 0x14, 0x18, 0x1C):
                address &= 0xF
            return self.palette_table[address]

        return self.cart.read(address & 0x3FFF) if self.cart else 0x00
