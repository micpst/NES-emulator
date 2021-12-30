
import os
import sys
import pygame as pg
from typing import Tuple

from nes.bus import Bus


MIN_SCREEN_WIDTH: int = 600
MIN_SCREEN_HEIGHT: int = 600
MIN_SCREEN_SIZE: Tuple[int, int] = (MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT)
MAIN_DIR: str = os.path.split(os.path.abspath(__file__))[0]


def load_image(file: str) -> pg.Surface:
    """
    Loads an image, prepares it for play.
    """
    file = os.path.join(MAIN_DIR, "data", "img", file)
    try:
        return pg.image.load(file)
    except pg.error:
        raise SystemExit(f"Could not load image '{file}' {pg.get_error()}")


def scale_surface(src: pg.Surface, factor: int) -> pg.Surface:
    new_size: Tuple[int, int] = (src.get_width() * factor, src.get_height() * factor)
    return pg.transform.scale(src, new_size)


def main() -> None:
    # Initialize pygame:
    pg.init()

    # Set the display mode:
    flags: int = pg.RESIZABLE | pg.DOUBLEBUF
    depth: int = pg.display.mode_ok(MIN_SCREEN_SIZE, flags, 8)
    screen: pg.Surface = pg.display.set_mode(MIN_SCREEN_SIZE, flags, depth)

    # Decorate the game window:
    pg.display.set_icon(load_image("nes.png"))
    pg.display.set_caption("NES emulator")
    pg.mouse.set_visible(False)

    clock: pg.time.Clock = pg.time.Clock()
    running: bool = True

    # Set up the NES:
    nes: Bus = Bus()
    nes.reset()

    # Start the main loop:
    while running:
        for e in pg.event.get():
            if e.type == pg.QUIT or \
               e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                # Exit the main loop:
                running = False

            elif e.type == pg.KEYDOWN and e.key == pg.K_f:
                # Toggle full-screen mode:
                screen = pg.display.set_mode(MIN_SCREEN_SIZE, flags=screen.get_flags() ^ pg.FULLSCREEN)

            elif e.type == pg.WINDOWSIZECHANGED:
                # Validate screen size:
                e.x = max(e.x, MIN_SCREEN_WIDTH)
                e.y = max(e.y, MIN_SCREEN_HEIGHT)

                # Resize without emitting events:
                screen = pg.display.set_mode((e.x, e.y), screen.get_flags())
                pg.event.get([pg.VIDEORESIZE, pg.WINDOWSIZECHANGED])

        while not nes.ppu.frame_complete:
            nes.clock()
        nes.ppu.frame_complete = False

        screen.blit(scale_surface(nes.ppu.screen, 2), (0, 0))
        pg.display.update()

        # Cap the frame rate at 120fps:
        clock.tick(120)

        # Update window caption:
        pg.display.set_caption(f"NES emulator - FPS: {int(clock.get_fps())}")

    # Quit the program:
    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
