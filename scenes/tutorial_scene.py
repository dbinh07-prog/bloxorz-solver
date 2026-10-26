"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""

from pathlib import Path
from ursina import Entity, Text, color, mouse, clamp, camera, destroy

from ui.glow_text import GlowText
from ui.menu_button import MenuTextButton
from ui.theme import (
    FONT_TITLE,
    FONT_BOLD,
    FONT_REGULAR,
    WHITE,
    GRAY,
    PRIMARY,
    DARK_PANEL,
    BACKGROUND,
    GLOW_TEXT_COLOR,
    GLOW_HALO_RGB,
)


class TutorialScene(Entity):

    ITEM_SPACING = 0.22
    SCROLL_STEP = 0.12
    DRAG_SPEED = 1.8

    def __init__(self, on_back):
        super().__init__()

        self.on_back = on_back
        self.is_dragging = False
        self.last_mouse_y = 0.0
        self.scroll_y = 0.0

        # Root chứa toàn bộ giao diện trong camera.ui
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

        # Tấm chắn phía trên Header che nội dung khi cuộn lên cao
        self.header_mask = Entity(
            parent=self.ui_root,
            model="quad",
            color=BACKGROUND,
            scale=(camera.aspect_ratio * 2, 0.20),
            position=(0, 0.42, -0.04),
        )

        # Tiêu đề màn hình hướng dẫn (z = -0.07)
        self.title = GlowText(
            text="HOW TO PLAY",
            font=FONT_TITLE,
            parent=self.ui_root,
            origin=(0, 0),
            position=(0, 0.43, -0.07),
            scale=1.4,
            main_color=GLOW_TEXT_COLOR,
            glow_rgb=GLOW_HALO_RGB,
        )

        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}

        # Dòng hướng dẫn cuộn trang (z = -0.07)
        self.hint = Text(
            text="Scroll mouse wheel / Arrow keys to read rules | ESC to go back",
            parent=self.ui_root,
            origin=(0, 0),
            position=(0, 0.365, -0.07),
            scale=0.68,
            color=GRAY,
            **font_kwargs,
        )

        # Nút quay về Main Menu đặt ở góc trái trên đồng bộ LevelSelectScene (z = -0.07)
        self.back_button = MenuTextButton(
            text="BACK",
            font=FONT_REGULAR,
            parent=self.ui_root,
            position=(-0.68, 0.42, -0.07),
            text_scale=1.1,
            label_origin=(0, 0),
            hitbox_origin=(0, 0),
            hitbox_width=0.22,
            on_click=self.go_back,
        )

        # Container chứa nội dung có thể cuộn
        self.content = Entity(
            parent=self.ui_root,
            position=(0, 0, 0),
        )

        self.create_tutorial_items()

        # Tính toán biên giới hạn cuộn
        content_height = len(self.tutorial_entries) * self.ITEM_SPACING
        visible_height = 0.58
        self.max_scroll_y = max(0.0, content_height - visible_height)

    def create_tutorial_items(self):
        """Khởi tạo danh sách các mục hướng dẫn điều khiển và cơ chế ô cờ."""
        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}
        font_bold_kwargs = {"font": FONT_BOLD or FONT_REGULAR} if (FONT_BOLD or FONT_REGULAR) else {}

        # Danh sách hướng dẫn: (image_path, badge_text, badge_color, title, description)
        self.tutorial_entries = [
            (
                "assets/sprites/wasd.png",
                "WASD",
                color.rgba32(18, 30, 50, 220),
                "CONTROLS: WASD / ARROW KEYS",
                "Roll the Bloxorz block along grid tiles. Tumble horizontally or vertically toward your goal.",
            ),
            (
                "assets/sprites/space.png",
                "SPACE",
                color.rgba32(18, 30, 50, 220),
                "SWITCH ACTIVE BLOCK: SPACE / TAB",
                "When split into two separate 1x1x1 cubes, press SPACE or TAB to switch control between cubes.",
            ),
            (
                "assets/texture/Tileset.png",
                "[ . ]",
                color.rgba32(24, 40, 60, 220),
                "FLOOR TILE [ . ]",
                "Standard solid floor. Safely supports the block in any orientation (standing upright or lying down).",
            ),
            (
                "assets/texture/fragile_tile.jpg",
                "[ F ]",
                color.rgba32(70, 30, 20, 220),
                "FRAGILE TILE [ F ]",
                "Weak tile that collapses under concentrated weight. Safe to roll over horizontally, but falls if block stands upright!",
            ),
            (
                "assets/texture/soft_switch.png",
                "( S )",
                color.rgba32(16, 50, 40, 220),
                "SOFT SWITCH ( S )",
                "Round button triggered by ANY contact. Standing upright or lying across it toggles linked bridges.",
            ),
            (
                "assets/texture/heavy_switch.png",
                "[ H ]",
                color.rgba32(60, 20, 50, 220),
                "HEAVY SWITCH [ H ]",
                "Heavy X-switch activated ONLY when the full block stands upright. Lying down will not trigger it.",
            ),
            (
                "assets/texture/split_switch.png",
                "[ X ]",
                color.rgba32(50, 45, 15, 220),
                "SPLIT SWITCH [ X ]",
                "Standing upright teleports and splits the block into two 1x1x1 cubes. Bring them adjacent to merge back!",
            ),
            (
                "assets/texture/bridge.jpg",
                "BRIDGE",
                color.rgba32(20, 35, 55, 220),
                "BRIDGES (BRG)",
                "Controllable path over void pits. Open bridge can be crossed; closed bridge behaves as empty abyss.",
            ),
            (
                "assets/texture/goal.png",
                "[ GOAL ]",
                color.rgba32(70, 15, 25, 220),
                "GOAL TILE (TARGET)",
                "Square hole exit. You win the stage ONLY when the block stands upright and drops directly into the goal!",
            ),
        ]

        start_y = 0.18
        for index, (img_path, badge_text, badge_col, title_text, desc_text) in enumerate(self.tutorial_entries):
            item_y = start_y - index * self.ITEM_SPACING

            # Khối Icon / Badge bên trái
            if Path(img_path).exists():
                Entity(
                    parent=self.content,
                    model="quad",
                    texture=img_path,
                    position=(-0.52, item_y, -0.015),
                    scale=(0.125, 0.125),
                    double_sided=True,
                )
            else:
                # Fallback badge phong cách Cyber nếu chưa có ảnh
                Entity(
                    parent=self.content,
                    model="quad",
                    color=badge_col,
                    position=(-0.52, item_y, -0.015),
                    scale=(0.18, 0.12),
                )
                Text(
                    parent=self.content,
                    text=badge_text,
                    origin=(0, 0),
                    position=(-0.52, item_y, -0.02),
                    scale=0.9,
                    color=PRIMARY,
                    **font_bold_kwargs,
                )

            # Tiêu đề mục hướng dẫn
            Text(
                parent=self.content,
                text=title_text,
                origin=(-0.5, 0),
                position=(-0.38, item_y + 0.035, -0.02),
                scale=0.82,
                color=PRIMARY,
                **font_bold_kwargs,
            )

            # Mô tả chi tiết luật
            Text(
                parent=self.content,
                text=desc_text,
                origin=(-0.5, 0),
                position=(-0.38, item_y - 0.025, -0.02),
                scale=0.68,
                color=WHITE,
                wordwrap=48,
                line_height=1.15,
                **font_kwargs,
            )

    def input(self, key):
        if key == "escape":
            self.go_back()
            return

        if key in ("scroll up", "up arrow"):
            self.scroll_by(-self.SCROLL_STEP)

        elif key in ("scroll down", "down arrow"):
            self.scroll_by(self.SCROLL_STEP)

        elif key == "left mouse down":
            self.is_dragging = True
            self.last_mouse_y = mouse.y

        elif key == "left mouse up":
            self.is_dragging = False

    def update(self):
        if hasattr(self, "background") and self.background:
            self.background.scale = (camera.aspect_ratio, 1)

        if not self.is_dragging:
            return

        current_mouse_y = mouse.y
        mouse_delta_y = current_mouse_y - self.last_mouse_y
        self.last_mouse_y = current_mouse_y

        # Kéo chuột để cuộn
        self.scroll_by(mouse_delta_y * self.DRAG_SPEED)

    def scroll_by(self, amount):
        self.scroll_y = clamp(
            self.scroll_y + amount,
            0.0,
            self.max_scroll_y,
        )
        self.content.y = self.scroll_y

    def go_back(self):
        if self.on_back:
            self.on_back()

    def on_destroy(self):
        if hasattr(self, "ui_root") and self.ui_root:
            destroy(self.ui_root)
            self.ui_root = None
