"""Camera isometric và hệ thống chiếu sáng 3D. Owner: thành viên 2."""

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
    """Định vị camera isometric nhìn vào tâm bàn cờ và dựng hệ thống ánh sáng 3D."""
    global _dir_light, _ambient_light

    # 1. Trích xuất kích thước bàn cờ an toàn
    rows = getattr(board, "rows", 0)
    cols = getattr(board, "cols", 0)
    if (rows <= 0 or cols <= 0) and hasattr(board, "grid") and board.grid:
        rows = len(board.grid)
        cols = len(board.grid[0]) if rows > 0 else 0

    if rows <= 0:
        rows = 10
    if cols <= 0:
        cols = 10

    # 2. Tính toán tâm bàn cờ theo quy ước grid_to_world: x = col, z = -row
    center_x = (cols - 1) / 2.0
    center_z = -(rows - 1) / 2.0
    target = Vec3(center_x, 0.0, center_z)

    # 3. Góc nhìn Isometric 3D (pitch = 48 độ dốc, yaw = -24 độ nghiêng góc nhìn)
    pitch = 48.0
    yaw = -24.0
    roll = 0.0

    camera.orthographic = False
    camera.fov = 45.0
    camera.rotation = (pitch, yaw, roll)

    # Khoảng cách camera tự động co giãn theo map lớn/nhỏ
    max_dim = max(rows, cols)
    distance = max(max_dim * 1.55 + 4.5, 12.0)
    camera.position = target - camera.forward * distance

    # 4. Hệ thống ánh sáng 3D tạo khối chiều sâu
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

    # Đèn định hướng (DirectionalLight) chiếu từ góc cao tạo bóng khối 3D rõ rệt
    _dir_light = DirectionalLight(
        rotation=(45, -35, 0),
        color=color.rgb32(255, 255, 255),
    )

    # Đèn môi trường (AmbientLight) dịu mắt phong cách Cyber
    _ambient_light = AmbientLight(
        color=color.rgb32(110, 125, 145),
    )
