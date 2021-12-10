from typing import Optional
from .cartridge import Cartridge


class PPU:
    """
    An emulation of the 2C02 picture processing unit.
    """

    def __init__(self) -> None:
        self.cart: Optional[Cartridge] = None

    def connect_cartridge(self, cart: Cartridge) -> None:
        self.cart = cart

    def clock(self) -> None:
        pass

    def write(self, address: int, data: int) -> None:
        pass

    def read(self, address: int, read_only: bool) -> int:
        return 0x00

    def _write(self, address: int, data: int) -> None:
        pass

    def _read(self, address: int, read_only: bool) -> int:
        return 0x00
