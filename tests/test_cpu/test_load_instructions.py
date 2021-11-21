import pytest
from nes.cpu import CPU
from nes.bus import Bus

@pytest.fixture
def nes():
    nes = Bus()
    
    # Set reset vector:
    nes.ram[0xFFFC] = 0x00
    nes.ram[0xFFFD] = 0x80
    
    # Reset:
    nes.cpu.reset()
    while nes.cpu.clock(): pass
    
    return nes

def check_unmodified_flags(status_reg, status_reg_copy):
    """
    Checks that the rest of the flags were not changed.
    """
    assert (status_reg & CPU.FLAGS.C.value) == (status_reg_copy & CPU.FLAGS.C.value)
    assert (status_reg & CPU.FLAGS.I.value) == (status_reg_copy & CPU.FLAGS.I.value)
    assert (status_reg & CPU.FLAGS.D.value) == (status_reg_copy & CPU.FLAGS.D.value)
    assert (status_reg & CPU.FLAGS.B.value) == (status_reg_copy & CPU.FLAGS.B.value)
    assert (status_reg & CPU.FLAGS.V.value) == (status_reg_copy & CPU.FLAGS.V.value)

@pytest.mark.parametrize(
    "value, Z, N",
    [
        (0x00, True, False),
        (0x37, False, False),
        (0x90, False, True),
    ],
    ids=["value=0x00", "value>0x00,<0x80", "value>=0x80"]
)
@pytest.mark.parametrize(
    "opcode, register",
    [
        (0xA9, "a_reg"),
        (0xA2, "x_reg"),
        (0xA0, "y_reg"),
    ],
    ids=["LDA", "LDX", "LDY"]
)
def test_load_register_IMM(nes, opcode, register, value, Z, N):
    """
    Tests immediate addressing mode for CPU load instructions.
    Checks that the correct value was loaded to the specified register and
    that the appropriate flag has been set after the given value was loaded.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = value
    
    # When:
    while nes.cpu.clock(): 
        cycles_used += 1
    
    # Then:
    assert cycles_used == 2
    assert getattr(nes.cpu, register) == value
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) == Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) == N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize(
    "opcode, register",
    [
        (0xA5, "a_reg"),
        (0xA6, "x_reg"),
        (0xA4, "y_reg"),
    ],
    ids=["LDA", "LDX", "LDY"]
)
def test_load_register_ZP0(nes, opcode, register):
    """
    Tests zero page addressing mode for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x42
    nes.ram[0x0042] = 0x37
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 3
    assert getattr(nes.cpu, register) == 0x37
    assert not (nes.cpu.status_reg & CPU.FLAGS.Z.value)
    assert not (nes.cpu.status_reg & CPU.FLAGS.N.value)
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize(
    "l, offset, address",
    [
        (0x42, 0x05, 0x0047),
        (0x80, 0xFF, 0x007F),
    ],
    ids=["not_wrapping_page", "wrapping_page"]
)
@pytest.mark.parametrize(
    "opcode, register, offset_register",
    [
        (0xB5, "a_reg", "x_reg"),
        (0xB6, "x_reg", "y_reg"),
        (0xB4, "y_reg", "x_reg"),
    ],
    ids=["LDA_X", "LDX_Y", "LDY_X"]
)
def test_load_register_ZP0_XY(nes, opcode, register, offset_register, l, offset, address):
    """
    Tests zero page addressing mode with X and Y offset for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    setattr(nes.cpu, offset_register, offset)
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = l
    nes.ram[address] = 0x37
    
    # When:
    while nes.cpu.clock(): 
        cycles_used += 1
    
    # Then:
    assert cycles_used == 4
    assert getattr(nes.cpu, register) == 0x37
    assert not (nes.cpu.status_reg & CPU.FLAGS.Z.value)
    assert not (nes.cpu.status_reg & CPU.FLAGS.N.value)
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)
    
@pytest.mark.parametrize(
    "opcode, register",
    [
        (0xAD, "a_reg"),
        (0xAE, "x_reg"),
        (0xAC, "y_reg"),
    ],
    ids=["LDA", "LDX", "LDY"]
)
def test_load_register_ABS(nes, opcode, register):
    """
    Tests absolute addressing mode for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x80
    nes.ram[0x8002] = 0x44
    nes.ram[0x4480] = 0x37
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 4
    assert getattr(nes.cpu, register) == 0x37
    assert not (nes.cpu.status_reg & CPU.FLAGS.Z.value)
    assert not (nes.cpu.status_reg & CPU.FLAGS.N.value)
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize(
    "l, h, offset, address, cycles",
    [
        (0x80, 0x44, 0x01, 0x4481, 4),
        (0xFF, 0x44, 0x01, 0x4500, 5),
    ],
    ids=["not_crossing_page", "crossing_page"]
)
@pytest.mark.parametrize(
    "opcode, register, offset_register",
    [
        (0xBD, "a_reg", "x_reg"),
        (0xBC, "y_reg", "x_reg"),
        (0xB9, "a_reg", "y_reg"),
        (0xBE, "x_reg", "y_reg"),
    ],
    ids=["LDA_X", "LDY_X", "LDA_Y", "LDX_Y"]
)
def test_load_register_ABS_XY(nes, opcode, register, offset_register, l, h, offset, address, cycles):
    """
    Tests absolute addressing mode with X and Y offset for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    setattr(nes.cpu, offset_register, offset)
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = l
    nes.ram[0x8002] = h
    nes.ram[address] = 0x37
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == cycles
    assert getattr(nes.cpu, register) == 0x37
    assert not (nes.cpu.status_reg & CPU.FLAGS.Z.value)
    assert not (nes.cpu.status_reg & CPU.FLAGS.N.value)
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize(
    "l_ptr, offset, ptr_address, l, h, address",
    [
        (0x02, 0x04, 0x0006, 0x00, 0x44, 0x4400),
        (0x80, 0xFF, 0x007F, 0x00, 0x44, 0x4400),
    ],
    ids=["LDA-not_wrapping_page", "LDA-wrapping_page"]
)
def test_load_register_IZX(nes, l_ptr, ptr_address, l, h, offset, address):
    """
    Tests indirect X addressing mode for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.cpu.x_reg = offset
    nes.ram[0x8000] = 0xA1
    nes.ram[0x8001] = l_ptr
    nes.ram[ptr_address] = l
    nes.ram[ptr_address + 1] = h
    nes.ram[address] = 0x37
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 6
    assert nes.cpu.a_reg == 0x37
    assert not (nes.cpu.status_reg & CPU.FLAGS.Z.value)
    assert not (nes.cpu.status_reg & CPU.FLAGS.N.value)
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize(
    "l_ptr, offset, ptr_address, l, h, address, cycles",
    [
        (0x02, 0x04, 0x0002, 0x00, 0x44, 0x4404, 5),
        (0x02, 0xFF, 0x0002, 0x80, 0x44, 0x457F, 6),
    ],
    ids=["LDA-not_crossing_page", "LDA-crossing_page"]
)
def test_load_register_IZY(nes, l_ptr, offset, ptr_address, l, h, address, cycles):
    """
    Tests indirect Y addressing mode for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.cpu.y_reg = offset
    nes.ram[0x8000] = 0xB1
    nes.ram[0x8001] = l_ptr
    nes.ram[ptr_address] = l
    nes.ram[ptr_address + 1] = h
    nes.ram[address] = 0x37
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == cycles
    assert nes.cpu.a_reg == 0x37
    assert not (nes.cpu.status_reg & CPU.FLAGS.Z.value)
    assert not (nes.cpu.status_reg & CPU.FLAGS.N.value)
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)