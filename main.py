from multiprocessing import freeze_support
from pathlib import Path
import os

from ursina import Ursina, application, color, window


def main() -> None:
    root = Path(__file__).resolve().parent
    os.chdir(root)
    application.asset_folder = root
    from app_controller import AppController
    from ui.theme import BACKGROUND

    app = Ursina(
        title="Bloxorz 3D - AI Solver",
        borderless=False,
        fullscreen=False,
        size=(1280, 720),
        development_mode=False,
    )

    try:
        window.center_on_screen()
    except Exception:
        pass

    window.color = BACKGROUND if BACKGROUND else color.rgb32(10, 14, 24)
    window.fps_counter.enabled = False
    window.exit_button.enabled = False

    _ = AppController()

    app.run()


if __name__ == "__main__":
    freeze_support()
    main()
