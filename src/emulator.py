import itertools
import os
import pygame as pg

from typing import Tuple, Dict
from pygame.locals import *

from nes.bus import Bus
from nes.cartridge import Cartridge
from nes.cpu import CPU


main_dir: str = os.path.split(os.path.abspath(__file__))[0]


def load_font(file: str, size: int) -> pg.font.Font:
    """
    Loads a font, prepares it for use.
    """
    file = os.path.join(main_dir, "data", "font", file)
    try:
        return pg.font.Font(file, size)
    except pg.error:
        raise SystemExit(f"Could not load font '{file}' {pg.get_error()}")


def load_image(file: str) -> pg.Surface:
    """
    Loads an image, prepares it for play.
    """
    file = os.path.join(main_dir, "data", "img", file)
    try:
        return pg.image.load(file)
    except pg.error:
        raise SystemExit(f"Could not load image '{file}' {pg.get_error()}")


def scale_surface(src: pg.Surface, factor: int) -> pg.Surface:
    """
    Loads an image, prepares it for play.
    """
    new_size: Tuple[int, int] = (src.get_width() * factor, src.get_height() * factor)
    return pg.transform.scale(src, new_size)


class TextPrint:
    """
    Enables print text on the screen.
    """

    def __init__(self, font_name: str, font_size: int) -> None:
        self.font: pg.font.Font = load_font(font_name, font_size)
        self.rect: pg.Rect = pg.Rect(0, 0, 0, 0)
        self.x: int = self.rect.x
        self.y: int = self.rect.y

    def print(self,
              screen: pg.Surface,
              text: str,
              text_color: pg.Color = pg.Color("white"),
              new_line: bool = True) -> None:

        if new_line:
            self.y += self.font.get_height()
            self.x = self.rect.x

        text_bitmap = self.font.render(text, True, text_color)
        screen.blit(text_bitmap, (self.x, self.y))

        if not new_line:
            self.x += text_bitmap.get_width()

    def set_rect(self, rect: pg.Rect) -> None:
        self.rect = rect
        self.x = self.rect.x
        self.y = self.rect.y


class NESEmulator:

    WIN_SIZE: Tuple[int, int] = (681, 522)
    DEBUG_WIN_SIZE: Tuple[int, int] = (1000, 522)

    def __init__(self) -> None:
        pg.init()

        self.running: bool = True
        self.debug_mode: bool = True

        self.nes: Bus = Bus()
        self.code: Dict[int, str] = {}
        self.text_printer: TextPrint = TextPrint("CascadiaMono.ttf", 22)

        self.screen: pg.Surface = pg.display.set_mode(self.get_window_size())
        self.clock: pg.time.Clock = pg.time.Clock()

        pg.display.set_icon(load_image("nes.png"))
        pg.display.set_caption("NES emulator")
        pg.mouse.set_visible(False)

        pg.event.set_allowed([KEYDOWN, QUIT])
        pg.key.set_repeat(400, 200)

    def get_window_size(self) -> Tuple[int, int]:
        return self.DEBUG_WIN_SIZE if self.debug_mode else self.WIN_SIZE

    def insert_cartridge(self, cart: Cartridge):
        """
        Connects cartridge to the NES and performs startup routine.
        """
        self.nes.insert_cartridge(cart)
        self.code = self.nes.cpu.disassemble(0x0000, 0xFFFF)
        self.nes.reset()

    def start(self):
        """
        Runs the main loop of the emulator.
        """
        while self.running:
            for ev in pg.event.get():
                if ev.type == QUIT or ev.type == KEYDOWN and ev.key == K_ESCAPE:
                    # Exit the main loop:
                    self.running = False

                elif ev.type == KEYDOWN and ev.key == K_F1:
                    # Toggle emulation debug mode:
                    self.debug_mode ^= True
                    self.screen = pg.display.set_mode(self.get_window_size())

                elif self.debug_mode:
                    if ev.type == KEYDOWN and ev.key == K_c:
                        # Emulate code step-by-step:
                        while True:
                            self.nes.clock()
                            if self.nes.cpu.instruction_completed():
                                break

                        # Drain additional system clock cycles out:
                        while True:
                            self.nes.clock()
                            if not self.nes.cpu.instruction_completed():
                                break

                    elif ev.type == KEYDOWN and ev.key == K_f:
                        # Emulate one frame:
                        while True:
                            self.nes.clock()
                            if self.nes.ppu.frame_completed() and self.nes.cpu.instruction_completed():
                                break

            # Run emulation:
            while not self.debug_mode:
                self.nes.clock()
                if self.nes.ppu.frame_completed():
                    break

            # Draw NES screen:
            self.screen.blit(scale_surface(self.nes.ppu.screen, 2), (0, 0))

            if self.debug_mode:
                # Draw additional debug components:
                self.draw_cpu(pg.Rect(690, 0, 269, 160))
                self.draw_code(pg.Rect(690, 160, 269, 372))

            pg.display.flip()

            # Cap the frame rate at 60 fps:
            self.clock.tick(60)

            # Update window caption:
            pg.display.set_caption(f"NES emulator - FPS: {int(self.clock.get_fps())}")

        # Quit the program:
        pg.quit()

    def draw_cpu(self, rect: pg.Rect) -> None:
        """
        Draws content of the CPU internal registers.
        """
        # Draw background:
        self.screen.fill(pg.Color("black"), rect)

        # Set initial text position:
        self.text_printer.set_rect(rect)

        # Print status register:
        self.text_printer.print(self.screen, "STATUS: ", new_line=False)

        # Print status register flags:
        for flag in CPU.FLAGS:
            color = pg.Color("white" if self.nes.cpu.status_reg & flag.value else "gray20")
            self.text_printer.print(self.screen, f"{flag.name} ", color, False)

        # Print rest of registers:
        self.text_printer.print(self.screen, f"A: ${format(self.nes.cpu.a_reg, '02x')}")
        self.text_printer.print(self.screen, f"X: ${format(self.nes.cpu.x_reg, '02x')}")
        self.text_printer.print(self.screen, f"Y: ${format(self.nes.cpu.y_reg, '02x')}")
        self.text_printer.print(self.screen, f"SP: ${format(self.nes.cpu.sp_reg, '02x')}")
        self.text_printer.print(self.screen, f"PC: ${format(self.nes.cpu.pc_reg, '04x')}")

    def draw_code(self, rect: pg.Rect) -> None:
        """
        Draws content of the CPU internal registers.
        """
        # Draw background:
        self.screen.fill(Color("black"), rect)

        # Set initial text position:
        self.text_printer.set_rect(rect)

        # Print current line of code to be executed:
        if self.nes.cpu.pc_reg in self.code:
            self.text_printer.print(self.screen, self.code[self.nes.cpu.pc_reg], pg.Color("cyan"))

            # Print next 12 lines of code:
            pc_index: int = list(self.code.keys()).index(self.nes.cpu.pc_reg)
            for line in list(self.code.values())[pc_index + 1:pc_index + 13]:
                self.text_printer.print(self.screen, line)


if __name__ == "__main__":
    emulator = NESEmulator()
    emulator.insert_cartridge(Cartridge("roms/super_mario_brothers.nes"))
    emulator.start()
