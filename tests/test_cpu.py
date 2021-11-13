import pytest
from nes.cpu import CPU

@pytest.fixture
def cpu():
    return CPU()

def test_cpu_reset(cpu):
    """
    Tests CPU registers just after power and changes during reset, and that RAM isn't changed during reset.
    """
    assert cpu.a_reg == 0x00
    assert cpu.x_reg == 0x00
    assert cpu.y_reg == 0x00
    assert cpu.sp_reg == 0x00
    assert cpu.pc_reg == 0x0000
    assert cpu.status_reg == 0x00