from enum import Enum
from typing import Dict, List, Optional, Type

from .mappers.mapper import Mapper
from .mappers.mapper_000 import Mapper000


class Cartridge:

    __slots__ = ("file_path", "prg_banks", "chr_banks", "prg_memory", "chr_memory", "mapper", "mirror", "valid_image")

    mappers: Dict[int, Type[Mapper]] = {
        0: Mapper000,
    }

    class MIRROR(Enum):
        HORIZONTAL = 0
        VERTICAL = 1

    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path

        self.prg_banks: int = 0
        self.chr_banks: int = 0
        self.prg_memory: List[int] = []
        self.chr_memory: List[int] = []

        self.mapper: Optional[Mapper] = None
        self.mirror: Cartridge.MIRROR = Cartridge.MIRROR.HORIZONTAL
        self.valid_image: bool = False

        try:
            with open(self.file_path, "rb") as f:
                # Read header - size 16B:
                name: bytes = f.read(4)
                prg_rom_chunks: int = int.from_bytes(f.read(1), "little")
                chr_rom_chunks: int = int.from_bytes(f.read(1), "little")
                mapper_1: int = int.from_bytes(f.read(1), "little")
                mapper_2: int = int.from_bytes(f.read(1), "little")
                prg_ram_size: bytes = f.read(1)
                tv_system_1: bytes = f.read(1)
                tv_system_2: bytes = f.read(1)
                unused: bytes = f.read(5)

                # Skip trainer:
                if mapper_1 & 0x04:
                    f.seek(512, 1)

                # Get program and character memory:
                self.prg_banks = prg_rom_chunks
                self.prg_memory = list(f.read(self.prg_banks * 16384))
                self.chr_banks = chr_rom_chunks
                self.chr_memory = list(f.read(self.chr_banks * 8192))

                # Load appropriate mapper:
                mapper_id: int = ((mapper_2 >> 4) << 4) | (mapper_1 >> 4)
                self.mapper = self.mappers[mapper_id](self.prg_banks, self.chr_banks)

                self.mirror = Cartridge.MIRROR.VERTICAL if mapper_1 & 0x01 else Cartridge.MIRROR.HORIZONTAL
                self.valid_image = True

        except OSError:
            pass

    def read(self, address: int) -> int:
        if self.mapper:
            mapped_address = self.mapper.map_read(address)
            if mapped_address != -0x0001:
                if 0x0000 <= address <= 0x1FFF:
                    return self.chr_memory[mapped_address]

                if 0x8000 <= address <= 0xFFFF:
                    return self.prg_memory[mapped_address]
        return 0x00

    def write(self, address: int, data: int) -> None:
        if self.mapper:
            mapped_address = self.mapper.map_write(address, data)
            if mapped_address != -0x0001:
                if 0x0000 <= address <= 0x1FFF:
                    self.chr_memory[mapped_address] = data

                elif 0x8000 <= address <= 0xFFFF:
                    self.prg_memory[mapped_address] = data
