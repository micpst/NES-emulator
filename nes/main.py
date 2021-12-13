import sys
import pygame as pg

from typing import Tuple, List


class App:

    MIN_SCREEN_WIDTH: int = 600
    MIN_SCREEN_HEIGHT: int = 600
    MIN_SCREEN_SIZE: Tuple[int, int] = (MIN_SCREEN_WIDTH, MIN_SCREEN_HEIGHT)

    @staticmethod
    def start() -> None:
        # Initialize pygame:
        pg.init()

        # Set the display mode:
        flags: int = pg.RESIZABLE
        depth: int = pg.display.mode_ok(App.MIN_SCREEN_SIZE, flags, 32)
        screen: pg.Surface = pg.display.set_mode(App.MIN_SCREEN_SIZE, flags, depth)

        # Decorate the game window:
        pg.display.set_caption("NES emulator")
        pg.mouse.set_visible(0)

        clock: pg.time.Clock = pg.time.Clock()
        running: bool = True

        all: pg.sprite.RenderUpdates = pg.sprite.RenderUpdates()

        # Start the main loop:
        while running:
            for e in pg.event.get():
                if e.type is pg.QUIT or e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                    # Exit the main loop:
                    running = False

                elif e.type == pg.KEYDOWN and e.key == pg.K_f:
                    # Toggle full-screen mode:
                    screen = pg.display.set_mode(flags=screen.get_flags() ^ pg.FULLSCREEN)

                elif e.type == pg.WINDOWSIZECHANGED:
                    # Validate screen size:
                    e.x = max(e.x, App.MIN_SCREEN_WIDTH)
                    e.y = max(e.y, App.MIN_SCREEN_HEIGHT)

                    # Resize without emitting events:
                    screen = pg.display.set_mode((e.x, e.y), screen.get_flags())
                    pg.event.get([pg.VIDEORESIZE, pg.WINDOWSIZECHANGED])

            # Update all the sprites:
            all.update()

            # Draw the scene:
            dirty: List[pg.Rect] = all.draw(screen)
            pg.display.update(dirty)

            # Cap the frame rate at 60fps:
            clock.tick(60)

        # Quit the program:
        pg.quit()
        sys.exit()


if __name__ == "__main__":
    App.start()
