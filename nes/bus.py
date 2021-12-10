from typing import List, Optional
from .cartridge import Cartridge


class Bus:
    """
    NES - System Bus.
    """
    
    def __init__(self) -> None:
        from .cpu import CPU
        from .ppu import PPU

        # Devices on the bus:
        self.cpu: CPU = CPU()
        self.ppu: PPU = PPU()
        self.ram: List[int] = [0x00] * 2048
        self.cart: Optional[Cartridge] = None

        # Helper variable:
        self._system_clock_count: int = 0

        # Connect bus to the CPU:
        self.cpu.connect_bus(self)

    def insert_cartridge(self, cart: Cartridge) -> None:
        self.cart = cart
        self.ppu.connect_cartridge(cart)

    def reset(self) -> None:
        self.cpu.reset()
        self._system_clock_count = 0

    def clock(self) -> None:
        self.ppu.clock()
        # The CPU runs 3 times slower than the PPU:
        if self._system_clock_count % 3 == 0:
            self.cpu.clock()
        self._system_clock_count += 1

    def write(self, address: int, data: int) -> None:
        # System RAM address range - mirrored every 2 kilobytes:
        if 0x0000 <= address <= 0x1FFF:
            self.ram[address & 0x07FF] = data

        # PPU address range - mirrored every 1 byte:
        elif 0x2000 <= address <= 0x3FFF:
            self.ppu.write(address & 0x0007, data)

        # Cartridge address range:
        elif self.cart:
            self.cart.write(address, data)
        
    def read(self, address: int, read_only: bool = False) -> int:
        # System RAM address range - mirrored every 2 kilobytes:
        if 0x0000 <= address <= 0x1FFF:
            return self.ram[address & 0x07FF]

        # PPU address range - mirrored every 1 byte:
        if 0x2000 <= address <= 0x3FFF:
            return self.ppu.read(address & 0x0007, read_only)

        # Cartridge address range:
        return self.cart.read(address) if self.cart else 0x00
