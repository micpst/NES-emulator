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
    Checks that the status registry flags have not been changed.
    """
    assert (status_reg & CPU.FLAGS.C.value) == (status_reg_copy & CPU.FLAGS.C.value)
    assert (status_reg & CPU.FLAGS.Z.value) == (status_reg_copy & CPU.FLAGS.Z.value)
    assert (status_reg & CPU.FLAGS.I.value) == (status_reg_copy & CPU.FLAGS.I.value)
    assert (status_reg & CPU.FLAGS.D.value) == (status_reg_copy & CPU.FLAGS.D.value)
    assert (status_reg & CPU.FLAGS.B.value) == (status_reg_copy & CPU.FLAGS.B.value)
    assert (status_reg & CPU.FLAGS.V.value) == (status_reg_copy & CPU.FLAGS.V.value)
    assert (status_reg & CPU.FLAGS.N.value) == (status_reg_copy & CPU.FLAGS.N.value)
    
@pytest.mark.parametrize(
    "opcode, register",
    [
        (0x85, "a_reg"),
        (0x86, "x_reg"),
        (0x84, "y_reg"),
    ],
    ids=["STA", "STX", "STY"]
)
def test_store_register_ZP0(nes, opcode, register):
    """
    Tests zero page addressing mode for CPU store instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    setattr(nes.cpu, register, 0x30)
    
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x40
    nes.ram[0x0040] = 0x00
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 3
    assert nes.ram[0x0040] == 0x30
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize(
    "opcode, register, offset_register",
    [
        (0x95, "a_reg", "x_reg"),
        (0x96, "x_reg", "y_reg"),
        (0x94, "y_reg", "x_reg"),
    ],
    ids=["X_STA", "Y_STX", "X_STY"]
)
def test_store_register_ZP(nes, opcode, register, offset_register):
    """
    Tests zero page addressing mode with X and Y offset for CPU store instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    setattr(nes.cpu, register, 0x30)
    setattr(nes.cpu, offset_register, 0x05)
    
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x40
    nes.ram[0x0045] = 0x00
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 4
    assert nes.ram[0x0045] == 0x30
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)

@pytest.mark.parametrize(
    "opcode, register",
    [
        (0x8D, "a_reg"),
        (0x8E, "x_reg"),
        (0x8C, "y_reg"),
    ],
    ids=["STA", "STX", "STY"]
)
def test_store_register_ABS(nes, opcode, register):
    """
    Tests absolute addressing mode for CPU store instructions.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    setattr(nes.cpu, register, 0x30)
    
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x80
    nes.ram[0x8002] = 0x44
    nes.ram[0x4480] = 0x00
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 4
    assert nes.ram[0x4480] == 0x30
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)
 
@pytest.mark.parametrize(
    "opcode, register, offset_register",
    [
        (0x9D, "a_reg", "x_reg"),
        (0x99, "a_reg", "y_reg"),
    ],
    ids=["X_STA", "Y_STA"]
)   
def test_store_register_AB(nes, opcode, register, offset_register):
    """
    Tests absolute addressing mode with X and Y offset for CPU STA instruction.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    setattr(nes.cpu, register, 0x30)
    setattr(nes.cpu, offset_register, 0x05)
    
    nes.ram[0x8000] = opcode
    nes.ram[0x8001] = 0x80
    nes.ram[0x8002] = 0x44
    nes.ram[0x4485] = 0x00
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 5
    assert nes.ram[0x4485] == 0x30
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)
    
def test_store_register_IZX_STA(nes):
    """
    Tests indirect X addressing mode for CPU STA instruction.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.cpu.x_reg = 0x05
    nes.cpu.a_reg = 0x30
    
    nes.ram[0x8000] = 0x81
    nes.ram[0x8001] = 0x80
    nes.ram[0x0085] = 0x00
    nes.ram[0x0086] = 0x44
    nes.ram[0x4400] = 0x00
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 6
    assert nes.ram[0x4400] == 0x30
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)
    
def test_store_register_IZY_STA(nes):
    """
    Tests indirect Y addressing mode for CPU STA instruction.
    """
    # Given:
    cycles_used = 1
    status_reg_copy = nes.cpu.status_reg
    nes.cpu.y_reg = 0x05
    nes.cpu.a_reg = 0x30
    
    nes.ram[0x8000] = 0x91
    nes.ram[0x8001] = 0x80
    nes.ram[0x0080] = 0x00
    nes.ram[0x0081] = 0x44
    nes.ram[0x4405] = 0x00
    
    # When:
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 6
    assert nes.ram[0x4405] == 0x30
    check_unmodified_flags(nes.cpu.status_reg, status_reg_copy)