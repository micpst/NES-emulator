from abc import ABCMeta, abstractmethod


class Mapper(metaclass=ABCMeta):

    def __init__(self, prg_banks: int, chr_banks: int):
        self.prg_banks: int = prg_banks
        self.chr_banks: int = chr_banks

    @abstractmethod
    def map_read(self, address: int) -> int:
        pass

    @abstractmethod
    def map_write(self, address: int, data: int) -> int:
        pass
