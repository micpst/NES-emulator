import pytest
from nes.cpu import CPU

values_to_be_loaded = [
    pytest.param(0x00, True, False, id="load_0x00"),
    pytest.param(0x37, False, False, id="load_0x37"),
    pytest.param(0x90, False, True, id="load_0x90"),
]

def check_unmodified_flags(status_reg, status_reg_copy):
    """
    Checks that the rest of the status registry flags have not been changed.
    """
    assert (status_reg & CPU.FLAGS.C.value) == (status_reg_copy & CPU.FLAGS.C.value)
    assert (status_reg & CPU.FLAGS.I.value) == (status_reg_copy & CPU.FLAGS.I.value)
    assert (status_reg & CPU.FLAGS.D.value) == (status_reg_copy & CPU.FLAGS.D.value)
    assert (status_reg & CPU.FLAGS.B.value) == (status_reg_copy & CPU.FLAGS.B.value)
    assert (status_reg & CPU.FLAGS.V.value) == (status_reg_copy & CPU.FLAGS.V.value)

@pytest.mark.parametrize("value, Z, N", values_to_be_loaded)
@pytest.mark.parametrize(
    "opcode, register",
    [
        pytest.param(0xA9, "a_reg", id="LDA"),
        pytest.param(0xA2, "x_reg", id="LDX"),
        pytest.param(0xA0, "y_reg", id="LDY"),
    ]
)
def test_load_register_IMM(nes, opcode, register, value, Z, N):
    """
    Tests immediate addressing mode for CPU load instructions.
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
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) is Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) is N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize("value, Z, N", values_to_be_loaded)
@pytest.mark.parametrize(
    "opcode, register", 
    [
        pytest.param(0xA5, "a_reg", id="LDA"),
        pytest.param(0xA6, "x_reg", id="LDX"),
        pytest.param(0xA4, "y_reg", id="LDY"),
    ]
)
def test_load_register_ZP0(nes, opcode, register, value, Z, N):
    """
    Tests zero page addressing mode for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x42
    nes.ram[0x0042] = value
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 3
    assert getattr(nes.cpu, register) == value
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) is Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) is N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize("value, Z, N", values_to_be_loaded)
@pytest.mark.parametrize(
    "l, offset, address",
    [
        pytest.param(0x42, 0x05, 0x0047, id="not_wrapping_page"),
        pytest.param(0x80, 0xFF, 0x007F, id="wrapping_page"),
    ]
)
@pytest.mark.parametrize(
    "opcode, register, offset_register", 
    [
        pytest.param(0xB5, "a_reg", "x_reg", id="X_LDA"),
        pytest.param(0xB6, "x_reg", "y_reg", id="Y_LDX"),
        pytest.param(0xB4, "y_reg", "x_reg", id="X_LDY"),
    ]
)
def test_load_register_ZP(nes, opcode, register, offset_register, l, offset, address, value, Z, N):
    """
    Tests zero page addressing mode with X and Y offset for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    setattr(nes.cpu, offset_register, offset)
    
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = l
    nes.ram[address] = value
    
    # When:
    while nes.cpu.clock(): 
        cycles_used += 1
    
    # Then:
    assert cycles_used == 4
    assert getattr(nes.cpu, register) == value
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) is Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) is N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize("value, Z, N", values_to_be_loaded)
@pytest.mark.parametrize(
    "opcode, register",
    [
        pytest.param(0xAD, "a_reg", id="LDA"),
        pytest.param(0xAE, "x_reg", id="LDX"),
        pytest.param(0xAC, "y_reg", id="LDY"),
    ]
)
def test_load_register_ABS(nes, opcode, register, value, Z, N):
    """
    Tests absolute addressing mode for CPU load instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x80
    nes.ram[0x8002] = 0x44
    nes.ram[0x4480] = value
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 4
    assert getattr(nes.cpu, register) == value
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) is Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) is N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize("value, Z, N", values_to_be_loaded)
@pytest.mark.parametrize(
    "l, h, offset, address, cycles", 
    [
        pytest.param(0x80, 0x44, 0x01, 0x4481, 4, id="not_crossing_page"),
        pytest.param(0xFF, 0x44, 0x01, 0x4500, 5, id="crossing_page"),
    ]
)
@pytest.mark.parametrize(
    "opcode, register, offset_register", 
    [
        pytest.param(0xBD, "a_reg", "x_reg", id="X_LDA"),
        pytest.param(0xBC, "y_reg", "x_reg", id="X_LDY"),
        pytest.param(0xB9, "a_reg", "y_reg", id="Y_LDA"),
        pytest.param(0xBE, "x_reg", "y_reg", id="Y_LDX"),
    ]
)
def test_load_register_AB(nes, opcode, register, offset_register, l, h, offset, address, cycles, value, Z, N):
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
    nes.ram[address] = value
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == cycles
    assert getattr(nes.cpu, register) == value
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) is Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) is N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize("value, Z, N", values_to_be_loaded) 
@pytest.mark.parametrize(
    "l_ptr, offset, ptr_address, l, h, address",
    [
        pytest.param(0x02, 0x04, 0x0006, 0x00, 0x44, 0x4400, id="not_wrapping_page"),
        pytest.param(0x80, 0xFF, 0x007F, 0x00, 0x44, 0x4400, id="wrapping_page"),
    ]
)
def test_load_register_IZX_LDA(nes, l_ptr, ptr_address, l, h, offset, address, value, Z, N):
    """
    Tests indirect X addressing mode for CPU LDA instruction.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.cpu.x_reg = offset
    
    nes.ram[0x8000] = 0xA1
    nes.ram[0x8001] = l_ptr
    nes.ram[ptr_address] = l
    nes.ram[ptr_address + 1] = h
    nes.ram[address] = value
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 6
    assert nes.cpu.a_reg == value
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) is Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) is N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize("value, Z, N", values_to_be_loaded)
@pytest.mark.parametrize(
    "l_ptr, offset, ptr_address, l, h, address, cycles",
    [
        pytest.param(0x02, 0x04, 0x0002, 0x00, 0x44, 0x4404, 5, id="not_crossing_page"),
        pytest.param(0x02, 0xFF, 0x0002, 0x80, 0x44, 0x457F, 6, id="crossing_page"),
    ]
)
def test_load_register_IZY_LDA(nes, l_ptr, offset, ptr_address, l, h, address, cycles, value, Z, N):
    """
    Tests indirect Y addressing mode for CPU LDA instruction.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.cpu.y_reg = offset
    
    nes.ram[0x8000] = 0xB1
    nes.ram[0x8001] = l_ptr
    nes.ram[ptr_address] = l
    nes.ram[ptr_address + 1] = h
    nes.ram[address] = value
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == cycles
    assert nes.cpu.a_reg == value
    assert bool(nes.cpu.status_reg & CPU.FLAGS.Z.value) is Z
    assert bool(nes.cpu.status_reg & CPU.FLAGS.N.value) is N
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)