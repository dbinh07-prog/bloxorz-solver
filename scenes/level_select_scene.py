import re
from pathlib import Path
from ursina import Entity, Text, camera, color, destroy

from scenes.algorithm_select_panel import AlgorithmSelectPanel
from ui.glow_text import GlowText
from ui.menu_button import MenuTextButton
from ui.theme import (
    FONT_TITLE,
    FONT_BOLD,
    FONT_REGULAR,
    WHITE,
    GRAY,
    BACKGROUND,
    GLOW_TEXT_COLOR,
    GLOW_HALO_RGB,
)


def get_level_number(path):
    p = Path(path) if not isinstance(path, Path) else path
    match = re.search(r"\d+", p.stem)
    if match:
        try:
            return int(match.group())
        except ValueError:
            return 999999
    return 999999


class LevelSelectScene(Entity):

    def __init__(self, mode, on_level_selected, on_back):
        super().__init__()

        self.mode = mode
        self.on_level_selected = on_level_selected
        self.on_back = on_back

        self.selected_level_path = None
        self.algorithm_panel = None

        self.ui_root = Entity(parent=camera.ui)

        menu_bg_candidates = [
            "assets/sprites/background_menu.png",
            "assets/sprites/Background_menu.png",
            "assets/sprites/background_menu.jpg",
            "assets/sprites/Background_menu.jpg",
            "assets/sprites/Background.png",
        ]
        bg_candidate = None
        for cand in menu_bg_candidates:
            if Path(cand).exists():
                bg_candidate = cand
                break

        if bg_candidate:
            self.background = Entity(
                parent=self.ui_root,
                model="quad",
                texture=bg_candidate,
                scale=(camera.aspect_ratio, 1),
                position=(0, 0, 1),
                double_sided=True,
            )
        else:
            self.background = Entity(
                parent=self.ui_root,
                model="quad",
                color=BACKGROUND,
                scale=(camera.aspect_ratio, 1),
                position=(0, 0, 1),
                double_sided=True,
            )

        title_text = "SELECT LEVEL" if mode == "play" else "SELECT LEVEL TO SOLVE"
        self.title = GlowText(
            text=title_text,
            font=FONT_TITLE,
            parent=self.ui_root,
            origin=(0, 0),
            position=(0, 0.42, -0.05),
            scale=1.4,
            main_color=GLOW_TEXT_COLOR,
            glow_rgb=GLOW_HALO_RGB,
        )

        self.back_button = MenuTextButton(
            text="BACK",
            font=FONT_REGULAR,
            parent=self.ui_root,
            position=(-0.68, 0.42, -0.05),
            text_scale=1.1,
            label_origin=(0, 0),
            hitbox_origin=(0, 0),
            hitbox_width=0.22,
            on_click=self.on_back,
        )

        self.level_container = Entity(parent=self.ui_root)

        self.create_level_buttons()

    def get_level_files(self):
        maps_dir = Path("maps")
        if not maps_dir.exists():
            return []

        json_files = [f for f in maps_dir.glob("*.json") if f.is_file()]
        json_files.sort(key=get_level_number)
        return json_files

    def create_level_buttons(self):
        level_files = self.get_level_files()
        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}

        if not level_files:
            Text(
                parent=self.level_container,
                text="No .json map files found in maps/ directory.",
                origin=(0, 0),
                position=(0, 0.1, -0.05),
                scale=0.85,
                color=color.rgb32(248, 113, 113),
                **font_kwargs,
            )
            return

        columns = 5
        spacing_x = 0.26
        spacing_y = 0.16
        text_scale = 1.15
        hitbox_width = 0.22

        for index, level_path in enumerate(level_files):
            row = index // columns
            col = index % columns

            x = (col - (columns - 1) / 2) * spacing_x
            y = 0.22 - row * spacing_y

            level_num = get_level_number(level_path)
            if level_num < 999999:
                btn_label = f"LV.{level_num}"
            else:
                stem_clean = level_path.stem.replace("example_", "").replace("level_", "").replace("_", " ").upper()
                btn_label = stem_clean[:10]

            button = MenuTextButton(
                text=btn_label,
                font=FONT_REGULAR,
                parent=self.level_container,
                position=(x, y, -0.02),
                text_scale=text_scale,
                label_origin=(0, 0),
                hitbox_origin=(0, 0),
                hitbox_width=hitbox_width,
                on_click=(lambda p=str(level_path): self.select_level(p)),
            )

    def select_level(self, level_path):
        if self.mode == "play":
            if self.on_level_selected:
                self.on_level_selected(level_path, "play", None)
        elif self.mode == "solve":
            self.open_algorithm_panel(level_path)

    def open_algorithm_panel(self, level_path):
        self.selected_level_path = level_path

        self.level_container.enabled = False
        self.back_button.enabled = False

        if self.algorithm_panel is not None:
            destroy(self.algorithm_panel)
            self.algorithm_panel = None

        self.algorithm_panel = AlgorithmSelectPanel(
            parent=self.ui_root,
            on_algorithm_selected=self.select_algorithm,
            on_close=self.close_algorithm_panel,
        )

    def select_algorithm(self, algorithm):
        if self.selected_level_path is None:
            return

        chosen_path = self.selected_level_path
        self.close_algorithm_panel()

        if self.on_level_selected:
            self.on_level_selected(chosen_path, "solve", algorithm)

    def close_algorithm_panel(self):
        if self.algorithm_panel is not None:
            destroy(self.algorithm_panel)
            self.algorithm_panel = None

        self.level_container.enabled = True
        self.back_button.enabled = True

    def update(self):
        if hasattr(self, "background") and self.background:
            self.background.scale = (camera.aspect_ratio, 1)

    def on_destroy(self):
        self.close_algorithm_panel()

        if hasattr(self, "ui_root") and self.ui_root:
            destroy(self.ui_root)
            self.ui_root = None
