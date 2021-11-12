from enum import Enum
from dataclasses import dataclass
from typing import Callable, List

import numpy as np

from .bus import Bus

class CPU:
    """
    An emulation of the 6502/2A03 processor.
    """
    
    class Flags(Enum):
        """
        The status register flags.
        """
        
        C = 1 << 0    # Carry Bit
        Z = 1 << 1    # Zero
        I = 1 << 2    # Disable Interrupts
        D = 1 << 3    # Decimal Mode
        B = 1 << 4    # Break
        U = 1 << 5    # Unused
        V = 1 << 6    # Overflow
        N = 1 << 7    # Negative
    
    @dataclass
    class _Instruction:
       name: str
       opcode: Callable[[], None]
       address_mode: Callable[[], None]
       cycles: np.int8
    
    def __init__(self) -> None:
        # CPU Core registers:
        self.a_reg      : np.uint8  = np.uint8(0x00)
        self.x_reg      : np.uint8  = np.uint8(0x00)
        self.y_reg      : np.uint8  = np.uint8(0x00)    
        self.sp_reg     : np.uint8  = np.uint8(0x00)
        self.pc_reg     : np.uint16 = np.uint16(0x0000)
        self.status_reg : np.uint8  = np.uint8(0x00)
        
        # Auxiliary variables to facilitate emulation:
        self._fetched     : np.uint8  = np.uint8(0x00)       # Working input value
        self._temp        : np.uint16 = np.uint16(0x0000)    # Convenience variable
        self._addr_abs    : np.uint16 = np.uint16(0x0000)    # All used memory addresses
        self._addr_rel    : np.uint16 = np.uint16(0x0000)    # Absolute address following a branch
        self._opcode      : np.uint8  = np.uint8(0x00)       # Instruction byte
        self._cycles      : np.uint8  = np.uint8(0)          # Instruction remaining cycles
        self._clock_count : np.uint32 = np.uint32(0)         # Global accumulation of the number of clocks
        
        self._lookup: List[CPU._Instruction] = []
        
    def _get_flag(self, flag: CPU.Flags) -> np.uint8:
        """
        Get status register flag.
        """
    
    def _set_flag(self, flag: CPU.Flags, value: np.uint8) -> None:
        """
        Set status register flag.
        """
    
    def _read(self, address: np.uint16) -> np.uint8:
        return self._bus.read(address)
    
    def _write(self, address: np.uint16, value: np.uint8) -> None:
        self._bus.write(address, value)
    
    def connect_bus(self, bus: Bus) -> None:
        self._bus: Bus = bus
    
    def reset_interrupt(self):
        """ 
        Forces CPU into known state.
        """
        
    def interrupt_request(self):
        """
        Executes an instruction at a specific location.
        """
        
    def nonmaskable_interrupt_request(self):
        """
        Similar to interrupt_request, but cannot be disabled.
        """
        
    def clock(self):
        """
        Perform one clock cycle's worth of update.
        """