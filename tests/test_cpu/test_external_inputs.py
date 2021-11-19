import pytest
from nes.cpu import CPU
from nes.bus import Bus

@pytest.fixture
def nes():
    return Bus()

def test_reset(nes):
    """
    Tests CPU registers just after power and changes during reset,
    and that RAM isn't changed during reset.
    """
    # After power up:
    assert nes.cpu.a_reg == 0x00
    assert nes.cpu.x_reg == 0x00
    assert nes.cpu.y_reg == 0x00
    assert nes.cpu.sp_reg == 0xFD
    assert nes.cpu.status_reg == 0x00 | CPU.FLAGS.U.value | CPU.FLAGS.I.value
    
    ram_cp = nes.ram.copy()
    nes.cpu.reset()
    
    # After reset:
    assert nes.ram == ram_cp
    assert nes.cpu.a_reg == 0x00
    assert nes.cpu.x_reg == 0x00
    assert nes.cpu.y_reg == 0x00
    assert nes.cpu.sp_reg == 0xFD
    assert nes.cpu.pc_reg == (nes.ram[0xFFFD] << 8) | nes.ram[0xFFFC]
    assert nes.cpu.status_reg == 0x00 | CPU.FLAGS.U.value | CPU.FLAGS.I.value
    
def test_interrupts(nes):
    """
    Tests the behavior and timing of CPU in the presence of interrupts,
    both IRQ and NMI.
    """
    # TODO Test IRQ 
    
    pc = nes.cpu.pc_reg
    nes.cpu.nonmaskable_interrupt_request()
    
    # Test stack content:
    assert nes.ram[0x0100 + nes.cpu.sp_reg + 3] == (pc >> 8) & 0x00FF
    assert nes.ram[0x0100 + nes.cpu.sp_reg + 2] == pc & 0x00FF
    assert nes.ram[0x0100 + nes.cpu.sp_reg + 1] == nes.cpu.status_reg
    
    # Test status register flags:
    assert not (nes.cpu.status_reg & CPU.FLAGS.B.value)
    assert nes.cpu.status_reg & CPU.FLAGS.U.value
    assert nes.cpu.status_reg & CPU.FLAGS.I.value
    
    # Test PC value:
    assert nes.cpu.pc_reg == (nes.ram[0xFFFB] << 8) | nes.ram[0xFFFA]