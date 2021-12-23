from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, List, NamedTuple

from .bus import Bus


class CPU:
    """
    An emulation of the 6502/2A03 processor.
    """

    class FLAGS(Enum):
        """
        The status register flags.
        """
        C = 1 << 0  # Carry Flag
        Z = 1 << 1  # Zero Flag
        I = 1 << 2  # Interrupt Disable
        D = 1 << 3  # Decimal Mode
        B = 1 << 4  # Break Command
        U = 1 << 5  # Unused
        V = 1 << 6  # Overflow Flag
        N = 1 << 7  # Negative Flag

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
        self.status_reg: int = 0x34

        # Helper variables:
        self._address: int = 0x0000  # Memory address
        self._opcode: int = 0x00     # Instruction byte
        self._cycles: int = 0        # Instruction remaining cycles
        self._clock_count: int = 0   # Global accumulation of the number of clocks

        self._lookup: List[CPU.INSTRUCTION] = [
            CPU.INSTRUCTION("BRK", self._BRK, self._IMM, 7), CPU.INSTRUCTION("ORA", self._ORA, self._IZX, 6),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 3), CPU.INSTRUCTION("ORA", self._ORA, self._ZP0, 3),
            CPU.INSTRUCTION("ASL", self._ASL, self._ZP0, 5), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("PHP", self._PHP, self._IMP, 3), CPU.INSTRUCTION("ORA", self._ORA, self._IMM, 2),
            CPU.INSTRUCTION("ASL", self._ASL, self._ACC, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 2),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("ORA", self._ORA, self._ABS, 4),
            CPU.INSTRUCTION("ASL", self._ASL, self._ABS, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("BPL", self._BPL, self._REL, 2), CPU.INSTRUCTION("ORA", self._ORA, self._IZY, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("ORA", self._ORA, self._ZPX, 4),
            CPU.INSTRUCTION("ASL", self._ASL, self._ZPX, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("CLC", self._CLC, self._IMP, 2), CPU.INSTRUCTION("ORA", self._ORA, self._ABY, 4),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("ORA", self._ORA, self._ABX, 4),
            CPU.INSTRUCTION("ASL", self._ASL, self._ABX, 7), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("JSR", self._JSR, self._ABS, 6), CPU.INSTRUCTION("AND", self._AND, self._IZX, 6),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("BIT", self._BIT, self._ZP0, 3), CPU.INSTRUCTION("AND", self._AND, self._ZP0, 3),
            CPU.INSTRUCTION("ROL", self._ROL, self._ZP0, 5), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("PLP", self._PLP, self._IMP, 4), CPU.INSTRUCTION("AND", self._AND, self._IMM, 2),
            CPU.INSTRUCTION("ROL", self._ROL, self._ACC, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 2),
            CPU.INSTRUCTION("BIT", self._BIT, self._ABS, 4), CPU.INSTRUCTION("AND", self._AND, self._ABS, 4),
            CPU.INSTRUCTION("ROL", self._ROL, self._ABS, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("BMI", self._BMI, self._REL, 2), CPU.INSTRUCTION("AND", self._AND, self._IZY, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("AND", self._AND, self._ZPX, 4),
            CPU.INSTRUCTION("ROL", self._ROL, self._ZPX, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("SEC", self._SEC, self._IMP, 2), CPU.INSTRUCTION("AND", self._AND, self._ABY, 4),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("AND", self._AND, self._ABX, 4),
            CPU.INSTRUCTION("ROL", self._ROL, self._ABX, 7), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("RTI", self._RTI, self._IMP, 6), CPU.INSTRUCTION("EOR", self._EOR, self._IZX, 6),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 3), CPU.INSTRUCTION("EOR", self._EOR, self._ZP0, 3),
            CPU.INSTRUCTION("LSR", self._LSR, self._ZP0, 5), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("PHA", self._PHA, self._IMP, 3), CPU.INSTRUCTION("EOR", self._EOR, self._IMM, 2),
            CPU.INSTRUCTION("LSR", self._LSR, self._ACC, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 2),
            CPU.INSTRUCTION("JMP", self._JMP, self._ABS, 3), CPU.INSTRUCTION("EOR", self._EOR, self._ABS, 4),
            CPU.INSTRUCTION("LSR", self._LSR, self._ABS, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("BVC", self._BVC, self._REL, 2), CPU.INSTRUCTION("EOR", self._EOR, self._IZY, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("EOR", self._EOR, self._ZPX, 4),
            CPU.INSTRUCTION("LSR", self._LSR, self._ZPX, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("CLI", self._CLI, self._IMP, 2), CPU.INSTRUCTION("EOR", self._EOR, self._ABY, 4),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("EOR", self._EOR, self._ABX, 4),
            CPU.INSTRUCTION("LSR", self._LSR, self._ABX, 7), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("RTS", self._RTS, self._IMP, 6), CPU.INSTRUCTION("ADC", self._ADC, self._IZX, 6),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 3), CPU.INSTRUCTION("ADC", self._ADC, self._ZP0, 3),
            CPU.INSTRUCTION("ROR", self._ROR, self._ZP0, 5), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("PLA", self._PLA, self._IMP, 4), CPU.INSTRUCTION("ADC", self._ADC, self._IMM, 2),
            CPU.INSTRUCTION("ROR", self._ROR, self._ACC, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 2),
            CPU.INSTRUCTION("JMP", self._JMP, self._IND, 5), CPU.INSTRUCTION("ADC", self._ADC, self._ABS, 4),
            CPU.INSTRUCTION("ROR", self._ROR, self._ABS, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("BVS", self._BVS, self._REL, 2), CPU.INSTRUCTION("ADC", self._ADC, self._IZY, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("ADC", self._ADC, self._ZPX, 4),
            CPU.INSTRUCTION("ROR", self._ROR, self._ZPX, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("SEI", self._SEI, self._IMP, 2), CPU.INSTRUCTION("ADC", self._ADC, self._ABY, 4),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("ADC", self._ADC, self._ABX, 4),
            CPU.INSTRUCTION("ROR", self._ROR, self._ABX, 7), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("STA", self._STA, self._IZX, 6),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("STY", self._STY, self._ZP0, 3), CPU.INSTRUCTION("STA", self._STA, self._ZP0, 3),
            CPU.INSTRUCTION("STX", self._STX, self._ZP0, 3), CPU.INSTRUCTION("???", self._XXX, self._IMP, 3),
            CPU.INSTRUCTION("DEY", self._DEY, self._IMP, 2), CPU.INSTRUCTION("???", self._NOP, self._IMP, 2),
            CPU.INSTRUCTION("TXA", self._TXA, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 2),
            CPU.INSTRUCTION("STY", self._STY, self._ABS, 4), CPU.INSTRUCTION("STA", self._STA, self._ABS, 4),
            CPU.INSTRUCTION("STX", self._STX, self._ABS, 4), CPU.INSTRUCTION("???", self._XXX, self._IMP, 4),
            CPU.INSTRUCTION("BCC", self._BCC, self._REL, 2), CPU.INSTRUCTION("STA", self._STA, self._IZY, 6),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("STY", self._STY, self._ZPX, 4), CPU.INSTRUCTION("STA", self._STA, self._ZPX, 4),
            CPU.INSTRUCTION("STX", self._STX, self._ZPY, 4), CPU.INSTRUCTION("???", self._XXX, self._IMP, 4),
            CPU.INSTRUCTION("TYA", self._TYA, self._IMP, 2), CPU.INSTRUCTION("STA", self._STA, self._ABY, 5),
            CPU.INSTRUCTION("TXS", self._TXS, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 5), CPU.INSTRUCTION("STA", self._STA, self._ABX, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 5), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("LDY", self._LDY, self._IMM, 2), CPU.INSTRUCTION("LDA", self._LDA, self._IZX, 6),
            CPU.INSTRUCTION("LDX", self._LDX, self._IMM, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("LDY", self._LDY, self._ZP0, 3), CPU.INSTRUCTION("LDA", self._LDA, self._ZP0, 3),
            CPU.INSTRUCTION("LDX", self._LDX, self._ZP0, 3), CPU.INSTRUCTION("???", self._XXX, self._IMP, 3),
            CPU.INSTRUCTION("TAY", self._TAY, self._IMP, 2), CPU.INSTRUCTION("LDA", self._LDA, self._IMM, 2),
            CPU.INSTRUCTION("TAX", self._TAX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 2),
            CPU.INSTRUCTION("LDY", self._LDY, self._ABS, 4), CPU.INSTRUCTION("LDA", self._LDA, self._ABS, 4),
            CPU.INSTRUCTION("LDX", self._LDX, self._ABS, 4), CPU.INSTRUCTION("???", self._XXX, self._IMP, 4),
            CPU.INSTRUCTION("BCS", self._BCS, self._REL, 2), CPU.INSTRUCTION("LDA", self._LDA, self._IZY, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("LDY", self._LDY, self._ZPX, 4), CPU.INSTRUCTION("LDA", self._LDA, self._ZPX, 4),
            CPU.INSTRUCTION("LDX", self._LDX, self._ZPY, 4), CPU.INSTRUCTION("???", self._XXX, self._IMP, 4),
            CPU.INSTRUCTION("CLV", self._CLV, self._IMP, 2), CPU.INSTRUCTION("LDA", self._LDA, self._ABY, 4),
            CPU.INSTRUCTION("TSX", self._TSX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 4),
            CPU.INSTRUCTION("LDY", self._LDY, self._ABX, 4), CPU.INSTRUCTION("LDA", self._LDA, self._ABX, 4),
            CPU.INSTRUCTION("LDX", self._LDX, self._ABY, 4), CPU.INSTRUCTION("???", self._XXX, self._IMP, 4),
            CPU.INSTRUCTION("CPY", self._CPY, self._IMM, 2), CPU.INSTRUCTION("CMP", self._CMP, self._IZX, 6),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("CPY", self._CPY, self._ZP0, 3), CPU.INSTRUCTION("CMP", self._CMP, self._ZP0, 3),
            CPU.INSTRUCTION("DEC", self._DEC, self._ZP0, 5), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("INY", self._INY, self._IMP, 2), CPU.INSTRUCTION("CMP", self._CMP, self._IMM, 2),
            CPU.INSTRUCTION("DEX", self._DEX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 2),
            CPU.INSTRUCTION("CPY", self._CPY, self._ABS, 4), CPU.INSTRUCTION("CMP", self._CMP, self._ABS, 4),
            CPU.INSTRUCTION("DEC", self._DEC, self._ABS, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("BNE", self._BNE, self._REL, 2), CPU.INSTRUCTION("CMP", self._CMP, self._IZY, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("CMP", self._CMP, self._ZPX, 4),
            CPU.INSTRUCTION("DEC", self._DEC, self._ZPX, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("CLD", self._CLD, self._IMP, 2), CPU.INSTRUCTION("CMP", self._CMP, self._ABY, 4),
            CPU.INSTRUCTION("NOP", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("CMP", self._CMP, self._ABX, 4),
            CPU.INSTRUCTION("DEC", self._DEC, self._ABX, 7), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("CPX", self._CPX, self._IMM, 2), CPU.INSTRUCTION("SBC", self._SBC, self._IZX, 6),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("CPX", self._CPX, self._ZP0, 3), CPU.INSTRUCTION("SBC", self._SBC, self._ZP0, 3),
            CPU.INSTRUCTION("INC", self._INC, self._ZP0, 5), CPU.INSTRUCTION("???", self._XXX, self._IMP, 5),
            CPU.INSTRUCTION("INX", self._INX, self._IMP, 2), CPU.INSTRUCTION("SBC", self._SBC, self._IMM, 2),
            CPU.INSTRUCTION("NOP", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._SBC, self._IMP, 2),
            CPU.INSTRUCTION("CPX", self._CPX, self._ABS, 4), CPU.INSTRUCTION("SBC", self._SBC, self._ABS, 4),
            CPU.INSTRUCTION("INC", self._INC, self._ABS, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("BEQ", self._BEQ, self._REL, 2), CPU.INSTRUCTION("SBC", self._SBC, self._IZY, 5),
            CPU.INSTRUCTION("???", self._XXX, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 8),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("SBC", self._SBC, self._ZPX, 4),
            CPU.INSTRUCTION("INC", self._INC, self._ZPX, 6), CPU.INSTRUCTION("???", self._XXX, self._IMP, 6),
            CPU.INSTRUCTION("SED", self._SED, self._IMP, 2), CPU.INSTRUCTION("SBC", self._SBC, self._ABY, 4),
            CPU.INSTRUCTION("NOP", self._NOP, self._IMP, 2), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
            CPU.INSTRUCTION("???", self._NOP, self._IMP, 4), CPU.INSTRUCTION("SBC", self._SBC, self._ABX, 4),
            CPU.INSTRUCTION("INC", self._INC, self._ABX, 7), CPU.INSTRUCTION("???", self._XXX, self._IMP, 7),
        ]

    def _get_flag(self, flag: CPU.FLAGS) -> bool:
        """
        Returns the state of a specific bit of the status register.
        """
        return (self.status_reg & flag.value) > 0

    def _set_flag(self, flag: CPU.FLAGS, value: bool) -> None:
        """
        Sets or resets a specific bit of the status register.
        """
        self.status_reg ^= (-value ^ self.status_reg) & flag.value

    def _read(self, address: int, read_only: bool = False) -> int:
        """
        Reads a byte from the bus at the specified address.
        """
        return self._bus.read(address, read_only)

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
        self.pc_reg = self._read(0xFFFC)
        self.pc_reg |= self._read(0xFFFD) << 8

        # Reset internal registers:
        self.a_reg = 0x00
        self.x_reg = 0x00
        self.y_reg = 0x00
        self.sp_reg = 0xFD
        self.status_reg = 0x34

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
            self.pc_reg = self._read(0xFFFE)
            self.pc_reg |= self._read(0xFFFF) << 8

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
        self.pc_reg = self._read(0xFFFA)
        self.pc_reg |= self._read(0xFFFB) << 8

        # IRQs take time:
        self._cycles = 8

    def clock(self) -> int:
        """
        Perform one clock cycle's worth of update.
        """
        if self._cycles == 0:
            # Read next instruction byte:
            self._opcode = self._read(self.pc_reg)
            self.pc_reg += 1

            # Fetch intermediate data and perform the operation:
            extra_cycle1: int = self._lookup[self._opcode].address_mode()
            extra_cycle2: int = self._lookup[self._opcode].operate()

            # Set the required number of cycles:
            self._cycles = self._lookup[self._opcode].cycles + (extra_cycle1 & extra_cycle2)

        self._clock_count += 1
        self._cycles -= 1
        return self._cycles

    def _IMP(self) -> int:
        """
        Address Mode: Implied
        There is no additional data required for this instruction.
        """
        return 0

    def _ACC(self) -> int:
        """
        Address Mode: Accumulator
        Allows directly target the accumulator.
        """
        return 0

    def _IMM(self) -> int:
        """
        Address Mode: Immediate
        The instruction expects the next byte to be used as a value.
        """
        self._address = self.pc_reg
        self.pc_reg += 1
        return 0

    def _ZP0(self) -> int:
        """
        Address Mode: Zero Page
        Allows to absolutely address a location in first 0xFF bytes of address range.
        """
        self._address = self._read(self.pc_reg)
        self.pc_reg += 1
        self._address &= 0x00FF
        return 0

    def _ZPX(self) -> int:
        """
        Address Mode: Zero Page with X offset
        Same as ZP0, but the contents of the X register is added to the given 8-bit address.
        """
        self._address = self._read(self.pc_reg) + self.x_reg
        self.pc_reg += 1
        self._address &= 0x00FF
        return 0

    def _ZPY(self) -> int:
        """
        Address Mode: Zero Page with Y offset
        Same as ZPX, but uses Y register to offset.
        """
        self._address = self._read(self.pc_reg) + self.y_reg
        self.pc_reg += 1
        self._address &= 0x00FF
        return 0

    def _REL(self) -> int:
        """
        Address Mode: Relative
        The address must reside within -128 and 127 of the branch instruction.
        """
        self._address = self._read(self.pc_reg)
        self.pc_reg += 1

        if self._address & 0x80:
            self._address |= 0xFF00

        self._address += self.pc_reg

        if (self._address & 0xFF00) != (self.pc_reg & 0xFF00):
            return 2
        return 1

    def _ABS(self) -> int:
        """
        Address Mode: Absolute
        A full 16-bit address is loaded and used.
        """
        self._address = self._read(self.pc_reg)
        self.pc_reg += 1
        self._address |= self._read(self.pc_reg) << 8
        self.pc_reg += 1
        return 0

    def _ABX(self) -> int:
        """
        Address Mode: Absolute with X offset
        Same as ABS, but the contents of the X register is added to the given 16-bit address.
        """
        self._address = self._read(self.pc_reg)
        self.pc_reg += 1
        self._address |= self._read(self.pc_reg) << 8
        self.pc_reg += 1

        h = self._address & 0xFF00
        self._address += self.x_reg

        if (self._address & 0xFF00) != h:
            return 1
        return 0

    def _ABY(self) -> int:
        """
        Address Mode: Absolute with Y offset
        Same as ABX, but uses Y register to offset.
        """
        self._address = self._read(self.pc_reg)
        self.pc_reg += 1
        self._address |= self._read(self.pc_reg) << 8
        self.pc_reg += 1

        h = self._address & 0xFF00
        self._address += self.y_reg

        if (self._address & 0xFF00) != h:
            return 1
        return 0

    def _IND(self) -> int:
        """
        Address mode: Indirect
        The supplied 16-bit address is read to get the actual 16-bit address.
        """
        ptr = self._read(self.pc_reg)
        self.pc_reg += 1
        ptr |= self._read(self.pc_reg) << 8
        self.pc_reg += 1

        self._address = self._read(ptr)
        self._address |= (self._read(ptr & 0xFF00) if (ptr & 0x00FF) == 0x00FF
                          else self._read(ptr + 1)) << 8
        return 0

    def _IZX(self) -> int:
        """
        Address mode: Indirect X
        The supplied 8-bit address is offset by X register to index a location in page 0x00.
        The actual 16-bit address is read from this location.
        """
        ptr = self._read(self.pc_reg) + self.x_reg
        self.pc_reg += 1

        self._address = self._read(ptr & 0x00FF)
        self._address |= self._read((ptr + 1) & 0x00FF) << 8
        return 0

    def _IZY(self) -> int:
        """
        Address mode: Indirect Y
        The supplied 8-bit address indexes a location in page 0x00.
        The actual 16-bit address is read and Y register is added to it to offset it.
        """
        ptr = self._read(self.pc_reg)
        self.pc_reg += 1

        self._address = self._read(ptr & 0x00FF)
        self._address |= self._read((ptr + 1) & 0x00FF) << 8

        h = self._address & 0xFF00
        self._address += self.y_reg

        if (self._address & 0xFF00) != h:
            return 1
        return 0

    def _ADC(self) -> int:
        """
        Instruction: Add with Carry
        Function:    A = A + M + C
        Flags Out:   C, Z, V, N
        """
        m = self._read(self._address)
        temp = self.a_reg + m + self._get_flag(CPU.FLAGS.C)
        self._set_flag(CPU.FLAGS.C, temp > 0xFF)
        self._set_flag(CPU.FLAGS.V, ((~(self.a_reg ^ m) & (self.a_reg ^ temp)) & 0x0080) > 0)

        self.a_reg = temp & 0x00FF
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 1

    def _AND(self) -> int:
        """
        Instruction: Bitwise Logic AND
        Function:    A = A & M
        Flags Out:   Z, N
        """
        self.a_reg &= self._read(self._address)
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 1

    def _ASL(self) -> int:
        """
        Instruction: Arithmetic Shift Left
        Function:    A = A * 2, M = M * 2
        Flags Out:   C, Z, N
        """
        a_mode = self._lookup[self._opcode].address_mode == self._ACC
        m = self.a_reg if a_mode else self._read(self._address)

        m <<= 1
        self._set_flag(CPU.FLAGS.C, (m & 0xFF00) > 0)

        m &= 0x00FF
        self._set_flag(CPU.FLAGS.Z, m == 0x00)
        self._set_flag(CPU.FLAGS.N, (m & 0x80) > 0)

        if a_mode:
            self.a_reg = m
        else:
            self._write(self._address, m)
        return 0

    def _BCC(self) -> int:
        """
        Instruction: Branch if Carry Clear
        Function:    PC = address <- C == 0
        """
        if not self._get_flag(CPU.FLAGS.C):
            self.pc_reg = self._address
            return 2
        return 0

    def _BCS(self) -> int:
        """
        Instruction: Branch if Carry Set
        Function:    PC = address <- C == 1
        """
        if self._get_flag(CPU.FLAGS.C):
            self.pc_reg = self._address
            return 2
        return 0

    def _BEQ(self) -> int:
        """
        Instruction: Branch if Equal
        Function:    PC = address <- Z == 1
        """
        if self._get_flag(CPU.FLAGS.Z):
            self.pc_reg = self._address
            return 2
        return 0

    def _BIT(self) -> int:
        """
        Instruction: Bit Test
        Function:    A & M, V = M6, N = M7
        Flags Out:   N, V, Z
        """
        m = self._read(self._address)
        self._set_flag(CPU.FLAGS.Z, (self.a_reg & m) == 0x00)
        self._set_flag(CPU.FLAGS.V, (m & 0x40) > 0)
        self._set_flag(CPU.FLAGS.N, (m & 0x80) > 0)
        return 0

    def _BMI(self) -> int:
        """
        Instruction: Branch if Negative
        Function:    PC = address <- N == 1
        """
        if self._get_flag(CPU.FLAGS.N):
            self.pc_reg = self._address
            return 2
        return 0

    def _BNE(self) -> int:
        """
        Instruction: Branch if Not Equal
        Function:    PC = address <- Z == 0
        """
        if not self._get_flag(CPU.FLAGS.Z):
            self.pc_reg = self._address
            return 2
        return 0

    def _BPL(self) -> int:
        """
        Instruction: Branch if Positive
        Function:    PC = address <- N == 0
        """
        if not self._get_flag(CPU.FLAGS.N):
            self.pc_reg = self._address
            return 2
        return 0

    def _BRK(self) -> int:
        """
        Instruction: Force Interrupt
        Function:    Program Sourced Interrupt
        Flags out:   B
        """
        self.pc_reg += 1

        self._write(0x0100 + self.sp_reg, (self.pc_reg >> 8) & 0x00FF)
        self.sp_reg -= 1
        self._write(0x0100 + self.sp_reg, self.pc_reg & 0x00FF)
        self.sp_reg -= 1

        self._set_flag(CPU.FLAGS.B, True)
        self._write(0x0100 + self.sp_reg, self.status_reg)
        self.sp_reg -= 1

        self.pc_reg = self._read(0xFFFE)
        self.pc_reg |= self._read(0xFFFF) << 8
        return 0

    def _BVC(self) -> int:
        """
        Instruction: Branch if Overflow Clear
        Function:    PC = address <- V == 0
        """
        if not self._get_flag(CPU.FLAGS.V):
            self.pc_reg = self._address
            return 2
        return 0

    def _BVS(self) -> int:
        """
        Instruction: Branch if Overflow Set
        Function:    PC = address <- V == 1
        """
        if self._get_flag(CPU.FLAGS.V):
            self.pc_reg = self._address
            return 2
        return 0

    def _CLC(self) -> int:
        """
        Instruction: Clear Carry Flag
        Function:    C = 0
        Flags out:   C
        """
        self._set_flag(CPU.FLAGS.C, False)
        return 0

    def _CLD(self) -> int:
        """
        Instruction: Clear Decimal Mode
        Function:    D = 0
        Flags out:   D
        """
        self._set_flag(CPU.FLAGS.D, False)
        return 0

    def _CLI(self) -> int:
        """
        Instruction: Clear Interrupt Disable
        Function:    I = 0
        Flags out:   I
        """
        self._set_flag(CPU.FLAGS.I, False)
        return 0

    def _CLV(self) -> int:
        """
        Instruction: Clear Overflow Flag
        Function:    V = 0
        Flags out:   V
        """
        self._set_flag(CPU.FLAGS.V, False)
        return 0

    def _CMP(self) -> int:
        """
        Instruction: Compare Accumulator
        Function:    Z <- (A - M) == 0
        Flags Out:   C, Z, N
        """
        m = self._read(self._address)
        temp = (self.a_reg - m) & 0x00FF
        self._set_flag(CPU.FLAGS.C, self.a_reg >= m)
        self._set_flag(CPU.FLAGS.Z, temp == 0x00)
        self._set_flag(CPU.FLAGS.N, (temp & 0x80) > 0)
        return 1

    def _CPX(self) -> int:
        """
        Instruction: Compare X Register
        Function:    Z <- (X - M) == 0
        Flags Out:   C, Z, N
        """
        m = self._read(self._address)
        temp = (self.x_reg - m) & 0x00FF
        self._set_flag(CPU.FLAGS.C, self.x_reg >= m)
        self._set_flag(CPU.FLAGS.Z, temp == 0x00)
        self._set_flag(CPU.FLAGS.N, (temp & 0x80) > 0)
        return 0

    def _CPY(self) -> int:
        """
        Instruction: Compare Y Register
        Function:    Z <- (Y - M) == 0
        Flags Out:   C, Z, N
        """
        m = self._read(self._address)
        temp = (self.y_reg - m) & 0x00FF
        self._set_flag(CPU.FLAGS.C, self.y_reg >= m)
        self._set_flag(CPU.FLAGS.Z, temp == 0x00)
        self._set_flag(CPU.FLAGS.N, (temp & 0x80) > 0)
        return 0

    def _DEC(self) -> int:
        """
        Instruction: Decrement a Memory Location
        Function:    M = M - 1
        Flags Out:   Z, N
        """
        m = (self._read(self._address) - 1) & 0x00FF
        self._write(self._address, m)
        self._set_flag(CPU.FLAGS.Z, m == 0x00)
        self._set_flag(CPU.FLAGS.N, (m & 0x80) > 0)
        return 0

    def _DEX(self) -> int:
        """
        Instruction: Decrement the X Register
        Function:    X = X - 1
        Flags Out:   Z, N
        """
        self.x_reg = (self.x_reg - 1) & 0x00FF
        self._set_flag(CPU.FLAGS.Z, self.x_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.x_reg & 0x80) > 0)
        return 0

    def _DEY(self) -> int:
        """
        Instruction: Decrement the Y Register
        Function:    Y = Y - 1
        Flags Out:   Z, N
        """
        self.y_reg = (self.y_reg - 1) & 0x00FF
        self._set_flag(CPU.FLAGS.Z, self.y_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.y_reg & 0x80) > 0)
        return 0

    def _EOR(self) -> int:
        """
        Instruction: Bitwise Logic XOR
        Function:    A = A ^ M
        Flags Out:   Z, N
        """
        self.a_reg ^= self._read(self._address)
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 1

    def _INC(self) -> int:
        """
        Instruction: Increment a Memory Location
        Function:    M = M + 1
        Flags Out:   Z, N
        """
        m = (self._read(self._address) + 1) & 0x00FF
        self._write(self._address, m)
        self._set_flag(CPU.FLAGS.Z, m == 0x00)
        self._set_flag(CPU.FLAGS.N, (m & 0x80) > 0)
        return 0

    def _INX(self) -> int:
        """
        Instruction: Increment the X Register
        Function:    X = X + 1
        Flags Out:   Z, N
        """
        self.x_reg = (self.x_reg + 1) & 0x00FF
        self._set_flag(CPU.FLAGS.Z, self.x_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.x_reg & 0x80) > 0)
        return 0

    def _INY(self) -> int:
        """
        Instruction: Increment the Y Register
        Function:    Y = Y + 1
        Flags Out:   Z, N
        """
        self.y_reg = (self.y_reg + 1) & 0x00FF
        self._set_flag(CPU.FLAGS.Z, self.y_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.y_reg & 0x80) > 0)
        return 0

    def _JMP(self) -> int:
        """
        Instruction: Jump to Another Location
        Function:    PC = address
        """
        self.pc_reg = self._address
        return 0

    def _JSR(self) -> int:
        """
        Instruction: Jump to a Subroutine
        Function:    PC -> Stack, PC = address
        """
        self.pc_reg -= 1

        self._write(0x0100 + self.sp_reg, (self.pc_reg >> 8) & 0x00FF)
        self.sp_reg -= 1
        self._write(0x0100 + self.sp_reg, self.pc_reg & 0x00FF)
        self.sp_reg -= 1

        self.pc_reg = self._address
        return 0

    def _LDA(self) -> int:
        """
        Instruction: Load The Accumulator
        Function:    A = M
        Flags Out:   Z, N
        """
        self.a_reg = self._read(self._address)
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 1

    def _LDX(self) -> int:
        """
        Instruction: Load The X Register
        Function:    X = M
        Flags Out:   Z, N
        """
        self.x_reg = self._read(self._address)
        self._set_flag(CPU.FLAGS.Z, self.x_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.x_reg & 0x80) > 0)
        return 1

    def _LDY(self) -> int:
        """
        Instruction: Load The Y Register
        Function:    Y = M
        Flags Out:   Z, N
        """
        self.y_reg = self._read(self._address)
        self._set_flag(CPU.FLAGS.Z, self.y_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.y_reg & 0x80) > 0)
        return 1

    def _LSR(self) -> int:
        """
        Instruction: Logical Shift Right
        Function:    A = A / 2, M = M / 2
        Flags Out:   C, Z, N
        """
        a_mode = self._lookup[self._opcode].address_mode == self._ACC
        m = self.a_reg if a_mode else self._read(self._address)
        self._set_flag(CPU.FLAGS.C, (m & 0x0001) > 0)

        m = (m >> 1) & 0x00FF
        self._set_flag(CPU.FLAGS.Z, m == 0x00)
        self._set_flag(CPU.FLAGS.N, (m & 0x80) > 0)

        if a_mode:
            self.a_reg = m
        else:
            self._write(self._address, m)
        return 0

    def _NOP(self) -> int:
        """
        Instruction: No Operation
        """
        # None of the unofficial opcodes have been implemented yet.
        # Details on unofficial op codes here:
        # https://wiki.nesdev.org/w/index.php/CPU_unofficial_opcodes
        return 0

    def _ORA(self) -> int:
        """
        Instruction: Bitwise Logic OR
        Function:    A = A | M
        Flags Out:   Z, N
        """
        self.a_reg |= self._read(self._address)
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 1

    def _PHA(self) -> int:
        """
        Instruction: Push Accumulator to Stack
        Function:    A -> Stack
        """
        self._write(0x0100 + self.sp_reg, self.a_reg)
        self.sp_reg -= 1
        return 0

    def _PHP(self) -> int:
        """
        Instruction: Push Status Register to Stack
        Function:    Status -> Stack
        """
        self._write(0x0100 + self.sp_reg, self.status_reg)
        self.sp_reg -= 1
        return 0

    def _PLA(self) -> int:
        """
        Instruction: Pop Accumulator off Stack
        Function:    A <- Stack
        Flags Out:   Z, N
        """
        self.sp_reg += 1
        self.a_reg = self._read(0x0100 + self.sp_reg)
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 0

    def _PLP(self) -> int:
        """
        Instruction: Pop Status Register off Stack
        Function:    Status <- Stack
        """
        self.sp_reg += 1
        self.status_reg = self._read(0x0100 + self.sp_reg)
        return 0

    def _ROL(self) -> int:
        """
        Instruction: Rotate Left
        Flags Out:   C, Z, N
        """
        a_mode = self._lookup[self._opcode].address_mode == self._ACC
        m = self.a_reg if a_mode else self._read(self._address)

        m = (m << 1) | self._get_flag(CPU.FLAGS.C)
        self._set_flag(CPU.FLAGS.C, (m & 0xFF00) > 0)

        m &= 0x00FF
        self._set_flag(CPU.FLAGS.Z, m == 0x00)
        self._set_flag(CPU.FLAGS.N, (m & 0x80) > 0)

        if a_mode:
            self.a_reg = m
        else:
            self._write(self._address, m)
        return 0

    def _ROR(self) -> int:
        """
        Instruction: Rotate Right
        Flags Out:   C, Z, N
        """
        a_mode = self._lookup[self._opcode].address_mode == self._ACC
        m = self.a_reg if a_mode else self._read(self._address)

        temp = (self._get_flag(CPU.FLAGS.C) << 7) | (m >> 1)
        self._set_flag(CPU.FLAGS.C, (m & 0x0001) > 0)

        temp &= 0x00FF
        self._set_flag(CPU.FLAGS.Z, temp == 0x00)
        self._set_flag(CPU.FLAGS.N, (temp & 0x80) > 0)

        if a_mode:
            self.a_reg = temp
        else:
            self._write(self._address, temp)
        return 0

    def _RTI(self) -> int:
        """
        Instruction: Return from Interrupt
        Function:    Status <- Stack, PC <- Stack
        Flags Out:   All
        """
        self.sp_reg += 1
        self.status_reg = self._read(0x0100 + self.sp_reg)
        self.sp_reg += 1
        self.pc_reg = self._read(0x0100 + self.sp_reg)
        self.sp_reg += 1
        self.pc_reg |= self._read(0x0100 + self.sp_reg) << 8
        return 0

    def _RTS(self) -> int:
        """
        Instruction: Return from Subroutine
        Function:    PC <- Stack
        """
        self.sp_reg += 1
        self.pc_reg = self._read(0x0100 + self.sp_reg)
        self.sp_reg += 1
        self.pc_reg |= self._read(0x0100 + self.sp_reg) << 8
        self.pc_reg += 1
        return 0

    def _SBC(self) -> int:
        """
        Instruction: Subtract with Carry
        Function:    A = A - M - (1 - C)
        Flags Out:   C, Z, V, N
        """
        m = self._read(self._address) ^ 0x00FF
        temp = self.a_reg + m + self._get_flag(CPU.FLAGS.C)
        self._set_flag(CPU.FLAGS.C, temp > 0xFF)
        self._set_flag(CPU.FLAGS.V, ((~(self.a_reg ^ m) & (self.a_reg ^ temp)) & 0x0080) > 0)

        self.a_reg = temp & 0x00FF
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 1

    def _SEC(self) -> int:
        """
        Instruction: Set Carry Flag
        Function:    C = 1
        Flags out:   C
        """
        self._set_flag(CPU.FLAGS.C, True)
        return 0

    def _SED(self) -> int:
        """
        Instruction: Set Decimal Mode
        Function:    D = 1
        Flags out:   D
        """
        self._set_flag(CPU.FLAGS.D, True)
        return 0

    def _SEI(self) -> int:
        """
        Instruction: Set Interrupt Disable
        Function:    I = 1
        Flags out:   I
        """
        self._set_flag(CPU.FLAGS.I, True)
        return 0

    def _STA(self) -> int:
        """
        Instruction: Store A Register at Address
        Function:    M = A
        """
        self._write(self._address, self.a_reg)
        return 0

    def _STX(self) -> int:
        """
        Instruction: Store X Register at Address
        Function:    M = X
        """
        self._write(self._address, self.x_reg)
        return 0

    def _STY(self) -> int:
        """
        Instruction: Store Y Register at Address
        Function:    M = Y
        """
        self._write(self._address, self.y_reg)
        return 0

    def _TAX(self) -> int:
        """
        Instruction: Transfer Accumulator to X Register
        Function:    X = A
        Flags Out:   Z, N
        """
        self.x_reg = self.a_reg
        self._set_flag(CPU.FLAGS.Z, self.x_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.x_reg & 0x80) > 0)
        return 0

    def _TAY(self) -> int:
        """
        Instruction: Transfer Accumulator to Y Register
        Function:    Y = A
        Flags Out:   Z, N
        """
        self.y_reg = self.a_reg
        self._set_flag(CPU.FLAGS.Z, self.y_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.y_reg & 0x80) > 0)
        return 0

    def _TSX(self) -> int:
        """
        Instruction: Transfer Stack Pointer to X Register
        Function:    X = S
        Flags Out:   Z, N
        """
        self.x_reg = self.sp_reg
        self._set_flag(CPU.FLAGS.Z, self.x_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.x_reg & 0x80) > 0)
        return 0

    def _TXA(self) -> int:
        """
        Instruction: Transfer X Register to Accumulator
        Function:    A = X
        Flags Out:   Z, N
        """
        self.a_reg = self.x_reg
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 0

    def _TXS(self) -> int:
        """
        Instruction: Transfer X Register to Stack Pointer
        Function:    S = X
        """
        self.sp_reg = self.x_reg
        return 0

    def _TYA(self) -> int:
        """
        Instruction: Transfer Y Register to Accumulator
        Function:    A = Y
        Flags Out:   Z, N
        """
        self.a_reg = self.y_reg
        self._set_flag(CPU.FLAGS.Z, self.a_reg == 0x00)
        self._set_flag(CPU.FLAGS.N, (self.a_reg & 0x80) > 0)
        return 0

    def _XXX(self) -> int:
        """
        This function captures illegal opcodes.
        """
        return 0
