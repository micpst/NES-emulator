import pytest
from nes.bus import Bus

@pytest.fixture
def bus():
    return Bus()

def test_cpu_reset(bus):
    """
    Tests CPU registers just after power and changes during reset,
    and that RAM isn't changed during reset.
    """
    # After power up:
    assert bus.cpu.a_reg == 0x00
    assert bus.cpu.x_reg == 0x00
    assert bus.cpu.y_reg == 0x00
    assert bus.cpu.sp_reg == 0xFD
    assert bus.cpu.status_reg == 0x00 | bus.cpu.FLAGS.U.value | bus.cpu.FLAGS.I.value
    
    ram_cp = bus.ram.copy()
    bus.cpu.reset()
    
    # After reset:
    assert bus.ram == ram_cp
    assert bus.cpu.a_reg == 0x00
    assert bus.cpu.x_reg == 0x00
    assert bus.cpu.y_reg == 0x00
    assert bus.cpu.sp_reg == 0xFD
    assert bus.cpu.pc_reg == (bus.ram[0xFFFD] << 8) | bus.ram[0xFFFC]
    assert bus.cpu.status_reg == 0x00 | bus.cpu.FLAGS.U.value | bus.cpu.FLAGS.I.value
    
def test_cpu_interrupts(bus):
    """
    Tests the behavior and timing of CPU in the presence of interrupts,
    both IRQ and NMI.
    """
    # TODO Test IRQ 
    
    pc = bus.cpu.pc_reg
    bus.cpu.nonmaskable_interrupt_request()
    
    # Test stack content:
    assert bus.ram[0x0100 + bus.cpu.sp_reg + 3] == (pc >> 8) & 0x00FF
    assert bus.ram[0x0100 + bus.cpu.sp_reg + 2] == pc & 0x00FF
    assert bus.ram[0x0100 + bus.cpu.sp_reg + 1] == bus.cpu.status_reg
    
    # Test status register flags:
    assert not (bus.cpu.status_reg & bus.cpu.FLAGS.B.value)
    assert bus.cpu.status_reg & bus.cpu.FLAGS.U.value
    assert bus.cpu.status_reg & bus.cpu.FLAGS.I.value
    
    # Test PC value:
    assert bus.cpu.pc_reg == (bus.ram[0xFFFB] << 8) | bus.ram[0xFFFA]