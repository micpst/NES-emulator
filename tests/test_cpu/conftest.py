import pytest
from nes.bus import Bus

@pytest.fixture(scope="package")
def nes():
    return Bus()
    
@pytest.fixture(autouse=True)
def reset_nes(nes):
    # Set reset vector:
    nes.ram[0xFFFC] = 0x00
    nes.ram[0xFFFD] = 0x80
    
    # Reset:
    nes.cpu.reset()
    while nes.cpu.clock(): 
        pass
    
    return nes