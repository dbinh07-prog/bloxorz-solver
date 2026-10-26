"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""

from pathlib import Path
from ursina import Entity, color, time

from ui.theme import PRIMARY

# Khớp file texture nếu có sẵn trong assets/texture/, tự động fallback sang màu khối chuẩn
BLOCK_TEXTURE_PATH = "assets/texture/Block.jpg"


class RotatingCube(Entity):

    def __init__(self, spin_speed_y=45, spin_speed_x=12, **kwargs):
        texture = None
        cube_color = PRIMARY or color.rgb32(0, 210, 255)

        candidates = [BLOCK_TEXTURE_PATH, "assets/texture/Block.jpg", "assets/texture/block.jpg", "assets/texture/block.png"]
        for cand in candidates:
            if cand and Path(cand).exists():
                try:
                    texture = cand
                    cube_color = color.white
                    break
                except Exception:
                    pass

        options = dict(
            model="cube",
            texture=texture,
            color=cube_color,
            rotation=(20, -30, 0),
        )
        options.update(kwargs)
        super().__init__(**options)

        self.spin_speed_y = spin_speed_y
        self.spin_speed_x = spin_speed_x

    def update(self):
        self.rotation_y += self.spin_speed_y * time.dt
        self.rotation_x += self.spin_speed_x * time.dt
