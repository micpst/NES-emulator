from .mapper import Mapper


class Mapper000(Mapper):

    def __init__(self, prg_banks: int, chr_banks: int) -> None:
        super().__init__(prg_banks, chr_banks)

    def cpu_map_write(self, address: int, mapped_address: int) -> bool:
        pass

    def ppu_map_read(self, address: int, mapped_address: int) -> bool:
        pass

    def ppu_map_write(self, address: int, mapped_address: int) -> bool:
        pass

    def cpu_map_read(self, address: int, mapped_address: int) -> bool:
        pass
