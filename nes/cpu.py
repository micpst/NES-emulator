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
        operate: Callable[[], int]
        address_mode: Callable[[], int]
        cycles: int
    
    def __init__(self) -> None:
        # CPU internal registers:
        self.a_reg: int = 0x00
        self.x_reg: int = 0x00
        self.y_reg: int = 0x00   
        self.sp_reg: int = 0xFD
        self.pc_reg: int = 0x0000
        self.status_reg: int = 0x00 | CPU.FLAGS.U.value | CPU.FLAGS.I.value
        
        # Helper variables:
        self._fetched: int = 0x00    # Working input value
        self._temp: int = 0x0000     # Convenience variable
        self._addr_abs: int = 0x0000 # All used memory addresses
        self._addr_rel: int = 0x0000 # Absolute address following a branch
        self._opcode: int = 0x00     # Instruction byte
        self._cycles: int = 0        # Instruction remaining cycles
        self._clock_count: int = 0   # Global accumulation of the number of clocks
        
        self._lookup: List[CPU.INSTRUCTION] = []
    
    def _get_flag(self, flag: CPU.FLAGS) -> bool:
        """
        Returns the state of a specific bit of the status register.
        """
        return (self.status_reg & flag.value) > 0
    
    def _set_flag(self, flag: CPU.FLAGS, value: bool) -> None:
        """
        Sets or resets a specific bit of the status register.
        """
        if value:
            self.status_reg |= flag.value
        else:
            self.status_reg &= ~flag.value

    def _read(self, address: int) -> int:
        """
        Reads a byte from the bus at the specified address.
        """
        return self._bus.read(address)
    
    def _write(self, address: int, value: int) -> None:
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
        if not self._get_flag(CPU.FLAGS.I):
            # Push the program counter to the stack:
            self._write(0x0100 + self.sp_reg, (self.pc_reg >> 8) & 0x00FF)
            self.sp_reg -= 1
            self._write(0x0100 + self.sp_reg, self.pc_reg & 0x00FF)
            self.sp_reg -= 1

            # Set status register flags:
            self._set_flag(CPU.FLAGS.B, False)
            self._set_flag(CPU.FLAGS.U, True)
            self._set_flag(CPU.FLAGS.I, True)
            
            # Push the status register to the stack:
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

        # Set status register flags:
        self._set_flag(CPU.FLAGS.B, False)
        self._set_flag(CPU.FLAGS.U, True)
        self._set_flag(CPU.FLAGS.I, True)
        
        # Push the status register to the stack:
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
            self._set_flag(CPU.FLAGS.U, True)

            # Increment program counter:
            self.pc_reg += 1
            
            # Fetch intermediate data and perform the operation:
            additional_cycle1 = self._lookup[self._opcode].address_mode()
            additional_cycle2 = self._lookup[self._opcode].operate()

            # Set the required number of cycles:
            self._cycles = self._lookup[self._opcode].cycles + (additional_cycle1 & additional_cycle2)

            # Set the unused status flag bit to 1:
            self._set_flag(CPU.FLAGS.U, True)

        # Increment global clock count:
        self._clock_count += 1

        # Decrement the number of cycles remaining for this instruction:
        self._cycles -= 1
        
    def _IMP(self) -> int:
        """
        Address Mode: Implied
        There is no additional data required for this instruction.
        """
        return 0
    
    def _IMM(self) -> int:
        """
        Address Mode: Immediate
        The instruction expects the next byte to be used as a value.
        """  
        self._addr_abs = self.pc_reg
        self.pc_reg += 1
        return 0
    
    def _ZP0(self) -> int:
        """
        Address Mode: Zero Page
        Allows to absolutely address a location in first 0xFF bytes of address range.
        """
        self._addr_abs = self._read(self.pc_reg)
        self.pc_reg += 1
        self._addr_abs &= 0x00FF
        return 0
    
    def _ZPX(self) -> int:
        """
        Address Mode: Zero Page with X offset
        Same as ZP0, but the contents of the X register is added to the given byte address.
        """
        self._addr_abs = self._read(self.pc_reg) + self.x_reg
        self.pc_reg += 1
        self._addr_abs &= 0x00FF
        return 0
    
    def _ZPY(self) -> int:
        """
        Address Mode: Zero Page with Y offset
        Same as ZPX, but uses Y register to offset.
        """
        self._addr_abs = self._read(self.pc_reg) + self.y_reg
        self.pc_reg += 1
        self._addr_abs &= 0x00FF
        return 0
  
    def _REL(self) -> int:
        """
        Address Mode: Relative
        The address must reside within -128 and 127 of the branch instruction.
        """
        self._addr_rel = self._read(self.pc_reg)
        self.pc_reg += 1
        if self._addr_rel & 0x80:
            self._addr_rel |= 0xFF0
        return 0

    def _ABS(self) -> int:
        """
        Address Mode: Absolute
        A full 16-bit address is loaded and used.
        """
        l = self._read(self.pc_reg)
        self.pc_reg += 1
        h = self._read(self.pc_reg)
        self.pc_reg += 1
        self._addr_abs = (h << 8) | l
        return 0

    def _ABX(self) -> int:
        """
        Address Mode: Absolute with X offset
        A full 16-bit address is loaded and used.
        """
        l = self._read(self.pc_reg)
        self.pc_reg += 1
        h = self._read(self.pc_reg)
        self.pc_reg += 1

        self._addr_abs = (h << 8) | l
        self._addr_abs += self.x_reg

        if (self._addr_abs & 0xFF00) != (h << 8):
            return 1
        return 0

    def _ABY(self) -> int:
        """
        Address Mode: Absolute with Y offset
        A full 16-bit address is loaded and used.
        """
        l = self._read(self.pc_reg)
        self.pc_reg += 1
        h = self._read(self.pc_reg)
        self.pc_reg += 1

        self._addr_abs = (h << 8) | l
        self._addr_abs += self.y_reg

        if (self._addr_abs & 0xFF00) != (h << 8):
            return 1
        return 0

    def _IND(self) -> int:
        """
        Address mode: Indirect
        The supplied 16-bit address is read to get the actual 16-bit address.
        """
        l = self._read(self.pc_reg)
        self.pc_reg += 1
        h = self._read(self.pc_reg)
        self.pc_reg += 1
        ptr = (h << 8) | l

        # Simulate page boundary harware bug:
        if l == 0x00FF: 
            self._addr_abs = (self._read(ptr & 0xFF00) << 8) | self._read(ptr)
        # Behave normally:
        else:
            self._addr_abs = (self._read(ptr + 1) << 8) | self._read(ptr)

        return 0

    def _IZX(self) -> int:
        """
        Address mode: Indirect X
        The suplied 8-bit address is offset by X register to index a location in page 0x00.
        The actual 16-bit address is read from this location.
        """
        t = self._read(self.pc_reg)
        self.pc_reg += 1

        l = self._read((t + self.x_reg) & 0x00FF)
        h = self._read((t + self.x_reg + 1) & 0x00FF)
        self._addr_abs = (h << 8) | l

        return 0

    def _IZY(self) -> int:
        """
        Address mode: Indirect Y
        The supplied 8-bit  address indexes a location in page 0x00. Form here actual 16-bit
        address is read and the contents of Y register is added to it to offset it.
        """
        t = self._read(self.pc_reg)
        self.pc_reg += 1

        l = self._read(t & 0x00FF)
        h = self._read((t + 1) & 0x00FF)

        self._addr_abs = (h << 8) | l
        self._addr_abs += self.y_reg

        if (self._addr_abs & 0xFF00) != (h << 8):
            return 1
        return 0