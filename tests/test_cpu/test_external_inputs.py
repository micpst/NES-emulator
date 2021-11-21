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

def test_reset():
    """
    Tests CPU registers just after power and changes during reset,
    and that RAM isn't changed during reset.
    """
    # Given:
    cycles_used = 1
    nes = Bus()
    nes.ram[0xFFFC] = 0x00
    nes.ram[0xFFFD] = 0x80
    ram_cp = nes.ram.copy()
    
    # When:
    nes.cpu.reset()
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 8
    assert nes.ram == ram_cp
    assert nes.cpu.a_reg == 0x00
    assert nes.cpu.x_reg == 0x00
    assert nes.cpu.y_reg == 0x00
    assert nes.cpu.sp_reg == 0xFD
    assert nes.cpu.pc_reg == 0x8000
    assert nes.cpu.status_reg == 0x00 | CPU.FLAGS.U.value | CPU.FLAGS.I.value
    
def test_nonmaskable_interrupts(nes):
    """
    Tests the behavior and timing of CPU in the presence of interrupts - NMI.
    """
    # Given:
    cycles_used = 1
    nes.ram[0xFFFA] = 0x90
    nes.ram[0xFFFB] = 0xFF
    
    # When:
    nes.cpu.nonmaskable_interrupt_request()
    while nes.cpu.clock():
        cycles_used += 1
    
    # Then:
    assert cycles_used == 8
    assert nes.cpu.pc_reg == 0xFF90
    assert nes.ram[0x01FD] == 0x80
    assert nes.ram[0x01FC] == 0x00
    assert nes.ram[0x01FB] == nes.cpu.status_reg  
    assert not (nes.cpu.status_reg & CPU.FLAGS.B.value)
    assert nes.cpu.status_reg & CPU.FLAGS.U.value
    assert nes.cpu.status_reg & CPU.FLAGS.I.value