from ursina import (
    camera,
    destroy,
    color,
    DirectionalLight,
    AmbientLight,
    Vec3,
)

from board import Board

_dir_light = None
_ambient_light = None


def setup_camera(board: Board) -> None:
    global _dir_light, _ambient_light

    rows = getattr(board, "rows", 0)
    cols = getattr(board, "cols", 0)
    if (rows <= 0 or cols <= 0) and hasattr(board, "grid") and board.grid:
        rows = len(board.grid)
        cols = len(board.grid[0]) if rows > 0 else 0

    if rows <= 0:
        rows = 10
    if cols <= 0:
        cols = 10

    center_x = (cols - 1) / 2.0
    center_z = -(rows - 1) / 2.0
    target = Vec3(center_x, 0.0, center_z)

    pitch = 48.0
    yaw = -24.0
    roll = 0.0

    camera.orthographic = False
    camera.fov = 45.0
    camera.rotation = (pitch, yaw, roll)

    max_dim = max(rows, cols)
    distance = max(max_dim * 1.9 + 5.0, 12.0)
    camera.position = target - camera.forward * distance

    if _dir_light is not None:
        try:
            destroy(_dir_light)
        except Exception:
            pass
        _dir_light = None

    if _ambient_light is not None:
        try:
            destroy(_ambient_light)
        except Exception:
            pass
        _ambient_light = None

    _dir_light = DirectionalLight(
        rotation=(45, -35, 0),
        color=color.rgb32(255, 255, 255),
    )

    _ambient_light = AmbientLight(
        color=color.rgb32(110, 125, 145),
    )
