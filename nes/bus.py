from typing import List

import numpy as np

from .cpu import CPU

class Bus:
    """
    NES - System Bus.
    """
    
    def __init__(self) -> None:
        # Devices on the bus:
        self.cpu : CPU = CPU()
        self.ram : List[np.uint8] = [0x00] * 1024 * 64 # fake RAM for now
        
        # Connect CPU to the bus:
        self.cpu.connect_bus(self)
    
    def write(self, address: np.unit16, data: np.unit8) -> None:
        if 0x0000 <= address <= 0xFFFF:
            self.ram[address] = data
        
    def read(self, address: np.unit16, read_only: bool = False) -> np.uint8:
        if 0x0000 <= address <= 0xFFFF:
            return self.ram[address]
        return 0x00