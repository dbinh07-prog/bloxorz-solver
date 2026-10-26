"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""

from pathlib import Path
from ursina import Entity, Text, camera, application, destroy

from ui.glow_text import GlowText
from ui.menu_button import MenuTextButton
from ui.animations import stagger_slide_in
from ui.rotating_cube import RotatingCube
from ui.theme import (
    FONT_TITLE,
    FONT_REGULAR,
    GLOW_TEXT_COLOR,
    GLOW_HALO_RGB,
    TITLE_GLOW_RINGS,
    TITLE_SCALE,
    MENU_ITEM_SCALE,
    FOOTER_SCALE,
    GRAY,
    BACKGROUND,
    MENU_ITEM_SPACING,
)
from ui.layout import (
    MENU_X,
    TITLE_Y,
    MENU_LIST_START_Y,
    FOOTER_Y,
    CUBE_OFFSET_X,
    CUBE_OFFSET_Y,
)


class MenuScene(Entity):

    def __init__(self, on_play, on_solve, on_tutorial):
        super().__init__()

        self.on_play = on_play
        self.on_solve = on_solve
        self.on_tutorial = on_tutorial

        # Root chứa toàn bộ UI 2D trong camera.ui
        self.ui_root = Entity(parent=camera.ui)

        # Nền giao diện: ưu tiên ảnh Background_menu mới thêm
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

        # Tiêu đề game phát sáng
        self.title = GlowText(
            text="BLOXORZ",
            font=FONT_TITLE,
            parent=self.ui_root,
            origin=(-0.5, 0),
            position=(MENU_X, TITLE_Y, -0.01),
            main_color=GLOW_TEXT_COLOR,
            glow_rgb=GLOW_HALO_RGB,
            rings=TITLE_GLOW_RINGS,
            scale=TITLE_SCALE,
        )

        # Khối Bloxorz 3D xoay vòng trang trí cạnh logo
        self.logo_cube = RotatingCube(
            parent=self.ui_root,
            position=(
                MENU_X + CUBE_OFFSET_X,
                TITLE_Y + CUBE_OFFSET_Y,
                -0.02,
            ),
            scale=(0.095, 0.19, 0.095),
        )

        # Phụ đề giao diện
        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}
        self.subtitle = Text(
            text="AI PUZZLE SOLVER",
            parent=self.ui_root,
            origin=(-0.5, 0),
            position=(MENU_X, TITLE_Y - 0.08, -0.01),
            scale=0.95,
            color=GRAY,
            **font_kwargs,
        )

        # Danh sách menu chính
        menu_entries = [
            ("PLAY", self.on_play),
            ("AI SOLVER", self.on_solve),
            ("TUTORIAL", self.on_tutorial),
            ("EXIT", application.quit),
        ]

        self.menu_buttons = []
        for index, (label, callback) in enumerate(menu_entries):
            item_y = MENU_LIST_START_Y - index * MENU_ITEM_SPACING

            button = MenuTextButton(
                text=label,
                font=FONT_REGULAR,
                position=(MENU_X, item_y),
                on_click=callback,
                text_scale=MENU_ITEM_SCALE,
                parent=self.ui_root,
            )
            self.menu_buttons.append(button)

        # Footer thông tin đồ án
        self.footer = Text(
            text="Introduction to AI - BFS / IDS / UCS / A*",
            parent=self.ui_root,
            origin=(-0.5, 0),
            position=(MENU_X, FOOTER_Y, -0.01),
            scale=FOOTER_SCALE,
            color=GRAY,
            **font_kwargs,
        )

        # Hiệu ứng xuất hiện so le mượt mà
        stagger_slide_in(self.menu_buttons)

    def update(self):
        if hasattr(self, "background") and self.background:
            self.background.scale = (camera.aspect_ratio, 1)

    def on_destroy(self):
        if hasattr(self, "ui_root") and self.ui_root:
            destroy(self.ui_root)
            self.ui_root = None
