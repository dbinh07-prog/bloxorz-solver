"""Entry point Ursina. Owner: thành viên 2."""

from ursina import Ursina, color, window

from app_controller import AppController
from ui.theme import BACKGROUND


def main() -> None:
    """Khởi tạo Ursina và AppController khi chạy ứng dụng."""
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

    # Cấu hình cửa sổ ứng dụng
    window.color = BACKGROUND if BACKGROUND else color.rgb32(10, 14, 24)
    window.fps_counter.enabled = False
    window.exit_button.enabled = False

    # Khởi tạo bộ điều phối toàn ứng dụng
    _ = AppController()

    app.run()


if __name__ == "__main__":
    main()
