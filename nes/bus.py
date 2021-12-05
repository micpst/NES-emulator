from typing import List


class Bus:
    """
    NES - System Bus.
    """
    
    def __init__(self) -> None:
        from .cpu import CPU
        
        # Devices on the bus:
        self.cpu: CPU = CPU()
        self.ram: List[int] = [0x00] * 1024 * 64  # fake RAM for now
        
        # Connect CPU to the bus:
        self.cpu.connect_bus(self)
    
    def write(self, address: int, data: int) -> None:
        if 0x0000 <= address <= 0xFFFF:
            self.ram[address] = data
        
    def read(self, address: int, read_only: bool = False) -> int:
        if 0x0000 <= address <= 0xFFFF:
            return self.ram[address]
        return 0x00
