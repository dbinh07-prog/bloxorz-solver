from pathlib import Path

from ursina import (
    Entity,
    Text,
    Ursina,
    application,
    camera,
    color,
    destroy,
    window,
)
from ursina.models.procedural.quad import Quad

from game.audio_manager import AudioManager
from game.game import Game
from ui.theme import (
    BACKGROUND,
    FONT_BOLD,
    FONT_REGULAR,
    FONT_TITLE,
    GRAY,
    PRIMARY,
    WHITE,
)

MAP_BASIC = "maps/example_basic.json"
MAP_SPLIT = "maps/level_11.json" if Path("maps/level_11.json").exists() else "maps/example_basic.json"


class SandboxHarness(Entity):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.audio_manager = AudioManager()
        self.current_level_path = MAP_BASIC
        self.game = None
        self.hud_root = None

        self.create_sandbox_hud()
        self.load_level(self.current_level_path)

    def create_sandbox_hud(self):
        if self.hud_root:
            destroy(self.hud_root)

        font_kwargs = {}
        if FONT_REGULAR and Path(FONT_REGULAR).exists():
            font_kwargs["font"] = FONT_REGULAR

        font_bold_kwargs = {}
        if FONT_BOLD and Path(FONT_BOLD).exists():
            font_bold_kwargs["font"] = FONT_BOLD

        self.hud_root = Entity(parent=camera.ui)

        panel_width = 0.52
        panel_height = 0.28
        panel_x = -0.58
        panel_y = -0.32

        self.panel_bg = Entity(
            parent=self.hud_root,
            model=Quad(radius=0.02),
            scale=(panel_width, panel_height),
            position=(panel_x, panel_y, -0.01),
            color=color.rgba32(10, 15, 26, 220),
        )

        self.panel_border = Entity(
            parent=self.hud_root,
            model=Quad(radius=0.02, mode="line", thickness=1.5),
            scale=(panel_width, panel_height),
            position=(panel_x, panel_y, -0.02),
            color=color.rgba32(0, 210, 255, 120),
        )

        self.title_text = Text(
            parent=self.hud_root,
            text="BLOXORZ 3D SANDBOX (TASK 5.1)",
            origin=(-0.5, 0.5),
            position=(panel_x - panel_width / 2 + 0.02, panel_y + panel_height / 2 - 0.02, -0.05),
            scale=1.05,
            color=PRIMARY,
            **font_bold_kwargs,
        )

        self.map_info_text = Text(
            parent=self.hud_root,
            text="",
            origin=(-0.5, 0.5),
            position=(panel_x - panel_width / 2 + 0.02, panel_y + panel_height / 2 - 0.065, -0.05),
            scale=0.90,
            color=color.rgb32(250, 204, 21),
            **font_kwargs,
        )

        instructions = (
            "[WASD / Arrows]  : Lăn khối 3D\n"
            "[Space / Tab]    : Đổi cube khi SPLIT\n"
            "[R]              : Chơi lại (Restart)\n"
            "[1]              : Nạp map cơ bản (example_basic.json)\n"
            "[2]              : Nạp map Split 'X' (level_11.json)\n"
            "[M]              : Bật / Tắt BGM  |  [Esc] Thoát"
        )

        self.instructions_text = Text(
            parent=self.hud_root,
            text=instructions,
            origin=(-0.5, 0.5),
            position=(panel_x - panel_width / 2 + 0.02, panel_y + panel_height / 2 - 0.105, -0.05),
            scale=0.82,
            color=WHITE,
            **font_kwargs,
        )

        self.status_text = Text(
            parent=self.hud_root,
            text="BGM: ON | Status: READY",
            origin=(-0.5, 0.5),
            position=(panel_x - panel_width / 2 + 0.02, panel_y - panel_height / 2 + 0.035, -0.05),
            scale=0.78,
            color=color.rgb32(52, 211, 153),
            **font_bold_kwargs,
        )

    def update_hud(self):
        if hasattr(self, "map_info_text") and self.map_info_text:
            p = Path(self.current_level_path)
            is_split_map = "11" in p.name
            tag = "[2] ADVANCED (SPLIT SWITCH 'X')" if is_split_map else "[1] BASIC MAP"
            self.map_info_text.text = f"Active: {p.name} ({tag})"

        if hasattr(self, "status_text") and self.status_text:
            bgm_status = "MUTED" if getattr(self.audio_manager, "is_music_muted", False) else "ON"
            self.status_text.text = f"BGM: {bgm_status} | Core Engine: READY"

    def load_level(self, level_path):
        if self.game:
            self.game.on_destroy()
            destroy(self.game)
            self.game = None

        self.current_level_path = str(level_path)

        self.game = Game(
            level_path=self.current_level_path,
            mode="play",
            audio_manager=self.audio_manager,
            on_back=self.exit_sandbox,
        )

        self.update_hud()

    def toggle_bgm(self):
        if self.audio_manager:
            self.audio_manager.toggle_music()
            self.update_hud()

    def exit_sandbox(self):
        if self.game:
            self.game.on_destroy()
            destroy(self.game)
            self.game = None

        if self.hud_root:
            destroy(self.hud_root)
            self.hud_root = None

        application.quit()

    def input(self, key):
        if key in ("1", "raw[1]"):
            if self.current_level_path != MAP_BASIC:
                self.load_level(MAP_BASIC)
            return

        if key in ("2", "raw[2]"):
            if Path(MAP_SPLIT).exists() and self.current_level_path != MAP_SPLIT:
                self.load_level(MAP_SPLIT)
            return

        if key in ("m", "M"):
            self.toggle_bgm()
            return

        if key == "escape":
            self.exit_sandbox()
            return


def run_sandbox():
    app = Ursina(
        title="Bloxorz 3D - Sandbox Test Harness (Task 5.1)",
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
    window.fps_counter.enabled = True
    window.exit_button.enabled = False

    _ = SandboxHarness()

    app.run()


def main():
    run_sandbox()


if __name__ == "__main__":
    main()
