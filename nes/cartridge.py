from typing import Dict, List

from nes.mappers.mapper import Mapper
from nes.mappers.mapper_000 import Mapper000


class Cartridge:

    mappers: Dict[int, Mapper] = {
        0: Mapper000,
    }

    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path

        self.prg_banks: int = 0
        self.chr_banks: int = 0
        self.prg_memory: List[int] = []
        self.chr_memory: List[int] = []

        self.mapper_id: int = 0
        self.mapper: Mapper = None
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

                # Determine mapper id:
                self.mapper_id = ((mapper_2 >> 4) << 4) | (mapper_1 >> 4)
                # self.mirror = () if mapper_1 & 0x01 else ()

                # Get program and character memory:
                self.prg_banks = prg_rom_chunks
                self.prg_memory = list(f.read(self.prg_banks * 16384))
                self.chr_banks = chr_rom_chunks
                self.chr_memory = list(f.read(self.chr_banks * 8192))

                # Load appropriate mapper:
                self.mapper = self.mappers[self.mapper_id](self.prg_banks, self.chr_banks)
                self.valid_image = True

        except OSError:
            pass
