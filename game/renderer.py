"""Dựng bàn cờ 3D, quản lý các loại ô, switch, bridge và goal. Owner: thành viên 2."""

from pathlib import Path
from ursina import Entity, Vec3, color, destroy
from ursina.models.procedural.cylinder import Cylinder


class Renderer:

    def __init__(self, board, parent):
        self.board = board
        self.parent = parent

        self.tiles = {}
        self.bridge_entities = {}
        self.map_root = Entity(parent=parent)
        self.textures = {}

        self.check_textures()
        self.create_map()

    def check_textures(self):
        """Kiểm tra và lưu trữ đường dẫn texture sẵn có trong assets/texture/."""
        texture_candidates = {
            ".": ["assets/texture/Tileset.png", "assets/texture/tileset.png", "assets/texture/floor.png", "assets/texture/floor.jpg"],
            "F": ["assets/texture/fragile_tile.jpg", "assets/texture/fragile_tile.png", "assets/texture/fragile.png", "assets/texture/fragile.jpg"],
            "S": ["assets/texture/soft_switch.png", "assets/texture/soft_switch.jpg", "assets/texture/soft.png", "assets/texture/soft.jpg"],
            "H": ["assets/texture/heavy_switch.png", "assets/texture/heavy_switch.jpg", "assets/texture/heavy.png", "assets/texture/heavy.jpg"],
            "X": ["assets/texture/split_switch.png", "assets/texture/split_switch.jpg", "assets/texture/split.png", "assets/texture/split.jpg"],
            "bridge": ["assets/texture/bridge.jpg", "assets/texture/bridge.png"],
            "goal": ["assets/texture/goal.png", "assets/texture/goal.jpg"],
        }

        self.textures = {}
        for key, paths in texture_candidates.items():
            valid_path = None
            for p in paths:
                if Path(p).exists():
                    valid_path = p
                    break
            self.textures[key] = valid_path

        return self.textures

    def grid_to_world(self, row, col):
        """Quy ước: col tăng theo trục +X, row tăng theo trục -Z (x = col, z = -row)."""
        return Vec3(float(col), 0.0, float(-row))

    def get_tile_texture(self, tile_type):
        """Lấy texture tương ứng với loại ô nếu có sẵn trong thư mục assets."""
        return self.textures.get(tile_type, None)

    def _get_tile_type(self, r, c):
        try:
            return self.board.tile_type(r, c)
        except Exception:
            grid = getattr(self.board, "grid", None)
            if grid and 0 <= r < len(grid) and 0 <= c < len(grid[r]):
                return grid[r][c]
            return "#"

    def _is_goal(self, r, c):
        try:
            return self.board.is_goal(r, c)
        except Exception:
            goal = getattr(self.board, "goal", None)
            return goal is not None and tuple(goal) == (r, c)

    def _is_bridge(self, r, c):
        try:
            return self.board.is_bridge(r, c)
        except Exception:
            bridge_at = getattr(self.board, "bridge_at", {}) or {}
            return (r, c) in bridge_at

    def _get_bridge_id(self, r, c):
        bridge_at = getattr(self.board, "bridge_at", {}) or {}
        return bridge_at.get((r, c), "b1")

    def _is_fragile(self, r, c):
        try:
            return self.board.is_fragile(r, c)
        except Exception:
            return self._get_tile_type(r, c) == "F"

    def _get_switch(self, r, c):
        try:
            return self.board.get_switch(r, c)
        except Exception:
            switches = getattr(self.board, "switches", []) or []
            for s in switches:
                pos = s.get("position", ())
                if tuple(pos) == (r, c):
                    return s
            return None

    def create_map(self):
        """Khởi tạo toàn bộ mô hình 3D cho các ô trên bàn cờ."""
        if hasattr(self, "map_root") and self.map_root:
            destroy(self.map_root)

        self.map_root = Entity(parent=self.parent)
        self.tiles = {}
        self.bridge_entities = {}

        rows = getattr(self.board, "rows", 0)
        cols = getattr(self.board, "cols", 0)
        if (rows <= 0 or cols <= 0) and hasattr(self.board, "grid") and self.board.grid:
            rows = len(self.board.grid)
            cols = len(self.board.grid[0]) if rows > 0 else 0

        for r in range(rows):
            for c in range(cols):
                pos = self.grid_to_world(r, c)
                tt = self._get_tile_type(r, c)

                # 1. Ô đích (Goal hole)
                if self._is_goal(r, c):
                    self._create_goal_tile(r, c, pos)
                    continue

                # 2. Ô cầu (Bridge) - có thể nằm trên ô '#' theo metadata map
                if self._is_bridge(r, c):
                    bridge_id = self._get_bridge_id(r, c)
                    self._create_bridge_tile(r, c, pos, bridge_id)
                    continue

                # 3. Ô công tắc (Switch S, H, X) - có thể định nghĩa trong metadata
                sw = self._get_switch(r, c)
                if sw is not None or tt in ("S", "H", "X"):
                    sw_type = "soft"
                    if sw and "type" in sw:
                        sw_type = str(sw["type"]).lower()
                    elif tt == "H":
                        sw_type = "heavy"
                    elif tt == "X":
                        sw_type = "split"

                    self._create_switch_tile(r, c, pos, sw_type)
                    continue

                # 4. Ô nứt / dễ vỡ (Fragile)
                if self._is_fragile(r, c):
                    self._create_fragile_tile(r, c, pos)
                    continue

                # Bỏ qua khoảng trống abyss / void nếu không phải ô đặc biệt
                if tt in ("#", " ", ""):
                    continue

                # 5. Ô sàn tiêu chuẩn (Floor .)
                self._create_floor_tile(r, c, pos)

        # Cập nhật hiển thị cầu theo trạng thái ban đầu
        initial_states = getattr(self.board, "initial_bridge_states", ())
        self.refresh_bridge_states(initial_states)

    def _create_floor_tile(self, r, c, pos):
        tex = self.get_tile_texture(".")
        if tex:
            tile = Entity(
                parent=self.map_root,
                model="cube",
                texture=tex,
                scale=(0.96, 0.2, 0.96),
                position=(pos.x, -0.1, pos.z),
                color=color.white,
            )
        else:
            tile = Entity(
                parent=self.map_root,
                model="cube",
                scale=(0.96, 0.2, 0.96),
                position=(pos.x, -0.1, pos.z),
                color=color.rgb32(32, 44, 68),
            )
        self.tiles[(r, c)] = tile

    def _create_fragile_tile(self, r, c, pos):
        tex = self.get_tile_texture("F")
        if tex:
            tile = Entity(
                parent=self.map_root,
                model="cube",
                texture=tex,
                color=color.white,
                scale=(0.96, 0.2, 0.96),
                position=(pos.x, -0.1, pos.z),
            )
        else:
            tile = Entity(
                parent=self.map_root,
                model="cube",
                scale=(0.96, 0.14, 0.96),
                position=(pos.x, -0.07, pos.z),
                color=color.rgb32(234, 88, 12),
            )
        self.tiles[(r, c)] = tile

    def _create_bridge_tile(self, r, c, pos, bridge_id):
        tex = self.get_tile_texture("bridge")
        if tex:
            tile = Entity(
                parent=self.map_root,
                model="cube",
                texture=tex,
                color=color.white,
                scale=(0.96, 0.2, 0.96),
                position=(pos.x, -0.1, pos.z),
            )
        else:
            tile = Entity(
                parent=self.map_root,
                model="cube",
                scale=(0.96, 0.16, 0.96),
                position=(pos.x, -0.08, pos.z),
                color=color.rgb32(14, 165, 233),
            )
        self.tiles[(r, c)] = tile
        self.bridge_entities.setdefault(bridge_id, []).append(tile)

    def _create_switch_tile(self, r, c, pos, sw_type):
        sw_str = str(sw_type).lower()
        if sw_str in ("soft", "s"):
            tex_key = "S"
        elif sw_str in ("heavy", "h"):
            tex_key = "H"
        elif sw_str in ("split", "x"):
            tex_key = "X"
        else:
            tex_key = "S"

        tex = self.get_tile_texture(tex_key)
        if tex:
            base_tile = Entity(
                parent=self.map_root,
                model="cube",
                texture=tex,
                color=color.white,
                scale=(0.96, 0.2, 0.96),
                position=(pos.x, -0.1, pos.z),
            )
            self.tiles[(r, c)] = base_tile
            return

        base_tile = Entity(
            parent=self.map_root,
            model="cube",
            scale=(0.96, 0.2, 0.96),
            position=(pos.x, -0.1, pos.z),
            color=color.rgb32(32, 44, 68),
        )
        self.tiles[(r, c)] = base_tile

        if sw_str in ("soft", "s"):
            Entity(
                parent=self.map_root,
                model=Cylinder(resolution=16),
                scale=(0.48, 0.08, 0.48),
                position=(pos.x, 0.04, pos.z),
                color=color.rgb32(34, 211, 238),
            )
        elif sw_str in ("heavy", "h"):
            Entity(
                parent=self.map_root,
                model="cube",
                scale=(0.54, 0.09, 0.54),
                position=(pos.x, 0.045, pos.z),
                color=color.rgb32(245, 158, 11),
            )
        elif sw_str in ("split", "x"):
            Entity(
                parent=self.map_root,
                model="cube",
                scale=(0.48, 0.09, 0.48),
                rotation=(0, 45, 0),
                position=(pos.x, 0.045, pos.z),
                color=color.rgb32(168, 85, 247),
            )

    def _create_goal_tile(self, r, c, pos):
        tex = self.get_tile_texture("goal")
        if tex:
            tile = Entity(
                parent=self.map_root,
                model="cube",
                texture=tex,
                color=color.white,
                scale=(0.96, 0.2, 0.96),
                position=(pos.x, -0.1, pos.z),
            )
            self.tiles[(r, c)] = tile
            return

        # Hố đích 3D lõm sâu xuống fallback
        pit = Entity(
            parent=self.map_root,
            model="cube",
            scale=(0.96, 0.5, 0.96),
            position=(pos.x, -0.35, pos.z),
            color=color.rgb32(8, 10, 16),
        )
        # Đĩa sáng neon ở đáy hố
        Entity(
            parent=self.map_root,
            model="quad",
            scale=(0.7, 0.7),
            rotation=(90, 0, 0),
            position=(pos.x, -0.58, pos.z),
            color=color.rgb32(0, 210, 255),
        )
        # Viền neon quanh miệng hố
        Entity(
            parent=self.map_root,
            model="cube",
            scale=(0.96, 0.04, 0.96),
            position=(pos.x, -0.04, pos.z),
            color=color.rgb32(14, 165, 233),
        )
        self.tiles[(r, c)] = pit

    def refresh_bridge_states(self, bridge_states):
        """Cập nhật hiển thị mở/đóng cho các ô cầu dựa trên bridge_states."""
        try:
            states_dict = self.board.bridge_state_dict(bridge_states)
        except Exception:
            if isinstance(bridge_states, dict):
                states_dict = bridge_states
            elif isinstance(bridge_states, (list, tuple)):
                states_dict = dict(bridge_states)
            else:
                states_dict = {}

        for bridge_id, entities in self.bridge_entities.items():
            is_open = bool(states_dict.get(bridge_id, False))
            for entity in entities:
                entity.enabled = is_open
