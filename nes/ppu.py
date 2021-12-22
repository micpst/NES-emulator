import pygame as pg
from typing import Optional, List
from .cartridge import Cartridge


class PPU:
    """
    An emulation of the 2C02 picture processing unit.
    """

    def __init__(self) -> None:
        self.name_table: List[List[int]] = 2 * [1024 * [0x00]]
        self.pattern_table: List[List[int]] = 2 * [4096 * [0x00]]
        self.palette_table: List[int] = 32 * [0x00]
        self.cart: Optional[Cartridge] = None

        self._cycles: int = 0
        self._scanline: int = 0
        self._frame_complete: bool = False

    def connect_cartridge(self, cart: Cartridge) -> None:
        self.cart = cart

    def clock(self) -> None:
        self._cycles += 1
        if self._cycles >= 341:
            self._cycles = 0
            self._scanline += 1

            if self._scanline >= 261:
                self._scanline = -1
                self._frame_complete = True

    def write(self, address: int, data: int) -> None:
        if address == 0x0000:
            pass

        elif address == 0x0001:
            pass

        elif address == 0x0002:
            pass

        elif address == 0x0003:
            pass

        elif address == 0x0004:
            pass

        elif address == 0x0005:
            pass

        elif address == 0x0006:
            pass

        elif address == 0x0007:
            pass

    def read(self, address: int, read_only: bool) -> int:
        if address == 0x0000:
            pass

        elif address == 0x0001:
            pass

        elif address == 0x0002:
            pass

        elif address == 0x0003:
            pass

        elif address == 0x0004:
            pass

        elif address == 0x0005:
            pass

        elif address == 0x0006:
            pass

        elif address == 0x0007:
            pass

        return 0x00

    def _write(self, address: int, data: int) -> None:
        self.cart.write(address & 0x3FFF, data)

    def _read(self, address: int, read_only: bool) -> int:
        return self.cart.read(address & 0x3FFF)
