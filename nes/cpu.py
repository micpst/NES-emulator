from __future__ import annotations

from enum import Enum
from typing import Callable, List, NamedTuple

import numpy as np

from .bus import Bus

class CPU:
    """
    An emulation of the 6502/2A03 processor.
    """
    
    class FLAGS(Enum):
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
    
    class INSTRUCTION(NamedTuple):
        """ 
        A Tuple that holds information about instruction supported by the CPU.
        """
        name: str
        operate: Callable[[], np.uint8]
        address_mode: Callable[[], np.uint8]
        cycles: np.uint8

    def __init__(self) -> None:
        # CPU internal registers:
        self.a_reg      : np.uint8  = 0x00
        self.x_reg      : np.uint8  = 0x00
        self.y_reg      : np.uint8  = 0x00   
        self.sp_reg     : np.uint8  = 0xFD
        self.pc_reg     : np.uint16 = 0x0000
        self.status_reg : np.uint8  = 0x00 | CPU.FLAGS.U.value | CPU.FLAGS.I.value
        
        # Helper variables:
        self._fetched     : np.uint8  = 0x00      # Working input value
        self._temp        : np.uint16 = 0x0000    # Convenience variable
        self._addr_abs    : np.uint16 = 0x0000    # All used memory addresses
        self._addr_rel    : np.uint16 = 0x0000    # Absolute address following a branch
        self._opcode      : np.uint8  = 0x00      # Instruction byte
        self._cycles      : np.uint8  = 0         # Instruction remaining cycles
        self._clock_count : np.uint32 = 0         # Global accumulation of the number of clocks
        
        self._lookup: List[CPU.INSTRUCTION] = []
    
    def _get_flag(self, flag: CPU.FLAGS) -> np.uint8:
        """
        Returns the state of a specific bit of the status register.
        """
        return 1 if (self.status_reg & flag.value) > 0 else 0
    
    def _set_flag(self, flag: CPU.FLAGS, value: bool) -> None:
        """
        Sets or resets a specific bit of the status register.
        """
        if value:
            self.status_reg |= flag.value
        else:
            self.status_reg &= ~flag.value

    def _read(self, address: np.uint16) -> np.uint8:
        """
        Reads a byte from the bus at the specified address.
        """
        return self._bus.read(address)
    
    def _write(self, address: np.uint16, value: np.uint8) -> None:
        """
        Writes a byte to the bus at the specified address.
        """
        self._bus.write(address, value)
    
    def connect_bus(self, bus: Bus) -> None:
        self._bus: Bus = bus
    
    def reset(self) -> None:
        """ 
        Forces CPU into known state.
        """     
        # Read new program counter location from fixed address:
        self._addr_abs = 0xFFFC
        l = self._read(self._addr_abs + 0)
        h = self._read(self._addr_abs + 1)
        self.pc_reg = (h << 8) | l

        # Reset internal registers:
        self.a_reg = 0x00
        self.x_reg = 0x00
        self.y_reg = 0x00
        self.sp_reg = 0xFD
        self.status_reg = 0x00 | CPU.FLAGS.U.value | CPU.FLAGS.I.value

        # Clear helper variables:
        self._fetched = 0x00
        self._addr_abs = 0x0000
        self._addr_rel = 0x0000
        
        # Reset takes time:
        self._cycles = 8
        
    def interrupt_request(self) -> None:
        """
        Executes an instruction at a specific location.
        """
        if self._get_flag(CPU.FLAGS.I) == 0:
            # Push the program counter to the stack:
            self._write(0x0100 + self.sp_reg, (self.pc_reg >> 8) & 0x00FF)
            self.sp_reg -= 1
            self._write(0x0100 + self.sp_reg, self.pc_reg & 0x00FF)
            self.sp_reg -= 1

            # Then push the status register to the stack:
            self._set_flag(CPU.FLAGS.B, 0)
            self._set_flag(CPU.FLAGS.U, 1)
            self._set_flag(CPU.FLAGS.I, 1)
            self._write(0x0100 + self.sp_reg, self.status_reg)
            self.sp_reg -= 1

            # Read new program counter location from fixed address:
            self._addr_abs = 0xFFFE
            l = self._read(self._addr_abs + 0)
            h = self._read(self._addr_abs + 1)
            self.pc_reg = (h << 8) | l

            # IRQs take time:
            self._cycles = 7
        
    def nonmaskable_interrupt_request(self) -> None:
        """
        Similar to interrupt_request, but cannot be disabled.
        """
        # Push the program counter to the stack:
        self._write(0x0100 + self.sp_reg, (self.pc_reg >> 8) & 0x00FF)
        self.sp_reg -= 1
        self._write(0x0100 + self.sp_reg, self.pc_reg & 0x00FF)
        self.sp_reg -= 1

        # Then push the status register to the stack:
        self._set_flag(CPU.FLAGS.B, 0)
        self._set_flag(CPU.FLAGS.U, 1)
        self._set_flag(CPU.FLAGS.I, 1)
        self._write(0x0100 + self.sp_reg, self.status_reg)
        self.sp_reg -= 1

        # Read new program counter location from fixed address:
        self._addr_abs = 0xFFFA
        l = self._read(self._addr_abs + 0)
        h = self._read(self._addr_abs + 1)
        self.pc_reg = (h << 8) | l

        # IRQs take time:
        self._cycles = 8
        
    def clock(self) -> None:
        """
        Perform one clock cycle's worth of update.
        """
        if self._cycles == 0:
            # Read next instruction byte:
            self._opcode = self._read(self.pc_reg)
            
            # Set the unused status flag bit to 1:
            self._set_flag(CPU.FLAGS.U, 1)

            # Increment program counter:
            self.pc_reg += 1
            
            # Fetch intermediate data and perform the operation:
            additional_cycle1 = self._lookup[self._opcode].address_mode()
            additional_cycle2 = self._lookup[self._opcode].operate()

            # Set the required number of cycles:
            self._cycles = self._lookup[self._opcode].cycles + (additional_cycle1 & additional_cycle2)

            # Set the unused status flag bit to 1:
            self._set_flag(CPU.FLAGS.U, 1)

        # Increment global clock count:
        self._clock_count += 1

        # Decrement the number of cycles remaining for this instruction:
        self._cycles -= 1