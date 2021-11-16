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