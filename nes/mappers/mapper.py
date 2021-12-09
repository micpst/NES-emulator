from abc import ABCMeta, abstractmethod


class Mapper(metaclass=ABCMeta):

    def __init__(self, prg_banks: int, chr_banks: int):
        self.prg_banks: int = prg_banks
        self.chr_banks: int = chr_banks

    @abstractmethod
    def cpu_map_read(self, address: int, mapped_address: int) -> bool:
        return False

    @abstractmethod
    def cpu_map_write(self, address: int, mapped_address: int) -> bool:
        return False

    @abstractmethod
    def ppu_map_read(self, address: int, mapped_address: int) -> bool:
        return False

    @abstractmethod
    def ppu_map_write(self, address: int, mapped_address: int) -> bool:
        return False
