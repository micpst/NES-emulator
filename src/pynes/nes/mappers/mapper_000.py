from .mapper import Mapper


class Mapper000(Mapper):

    def __init__(self, prg_banks: int, chr_banks: int) -> None:
        super().__init__(prg_banks, chr_banks)

    def map_write(self, address: int) -> int:
        # There is no mapping required for PPU:
        if 0x0000 <= address <= 0x1FFF and self.chr_banks == 0:
            return address

        # Mapping for CPU:
        if 0x8000 <= address <= 0xFFFF:
            return address & (0x7FFF if self.prg_banks > 1 else 0x3FFF)

        return -0x0001

    def map_read(self, address: int) -> int:
        # There is no mapping required for PPU:
        if 0x0000 <= address <= 0x1FFF:
            return address

        # Mapping for CPU:
        if 0x8000 <= address <= 0xFFFF:
            return address & (0x7FFF if self.prg_banks > 1 else 0x3FFF)

        return -0x0001
