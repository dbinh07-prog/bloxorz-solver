"""Renderer và animation 3D cho khối Bloxorz và hai cube tách rời. Owner: thành viên 2."""

from pathlib import Path
from ursina import (
    Entity,
    Vec3,
    color,
    destroy,
    invoke,
    curve,
)

from block import Block, Orientation

# Đường dẫn texture tùy chọn nếu có file 1:1 chuẩn
BLOCK_TEXTURE_PATH = "assets/texture/Block.jpg"

# Bảng màu Cyber-3D cho khối khi chưa có file texture riêng
BLOCK_COLOR_STAND = color.rgb32(245, 158, 11)        # Vàng hổ phách Cyber
ACTIVE_CUBE_COLOR = color.rgb32(0, 225, 255)         # Neon Cyan rực rỡ cho cube đang chọn
INACTIVE_CUBE_COLOR = color.rgb32(30, 80, 130)       # Xanh thẫm tĩnh lặng cho cube không hoạt động


class BlockTransform:
    """Đóng gói dữ liệu vị trí, tỷ lệ và góc quay hỗ trợ cả unpack lẫn truy xuất thuộc tính."""

    def __init__(self, position, scale, rotation=None, split_info=None):
        self.position = position
        self.scale = scale
        self.rotation = rotation or Vec3(0, 0, 0)
        self.split_info = split_info

    def __iter__(self):
        yield self.position
        yield self.scale
        yield self.rotation

    def __getitem__(self, index):
        if index == 0:
            return self.position
        elif index == 1:
            return self.scale
        elif index == 2:
            return self.rotation
        raise IndexError(f"BlockTransform index out of range: {index}")


class BlockRenderer:

    def __init__(self, block_logic, parent):
        self.parent = parent
        self.current_block = block_logic

        # Root chứa toàn bộ khối
        self.root = Entity(parent=parent)

        # Kiểm tra file texture
        self.texture = None
        candidates = [BLOCK_TEXTURE_PATH, "assets/texture/Block.jpg", "assets/texture/block.jpg", "assets/texture/block.png"]
        for cand in candidates:
            if cand and Path(cand).exists():
                self.texture = cand
                break

        # Khối liền chính (dùng cho STANDING, HORIZONTAL, VERTICAL)
        self.block_entity = Entity(
            parent=self.root,
            model="cube",
            texture=self.texture,
            color=color.white if self.texture else BLOCK_COLOR_STAND,
        )

        # Hai cube con (dùng cho SPLIT)
        self.split_cube1 = Entity(
            parent=self.root,
            model="cube",
            texture=self.texture,
            color=ACTIVE_CUBE_COLOR,
            enabled=False,
        )
        self.split_cube2 = Entity(
            parent=self.root,
            model="cube",
            texture=self.texture,
            color=INACTIVE_CUBE_COLOR,
            enabled=False,
        )

        self._split_pivot = None
        self._split_moved_entity = None
        self._tipping_entity = None

        self.update_transform()

    def grid_to_world(self, row, col):
        """Đồng bộ 100% với Renderer: col tăng theo +X, row tăng theo -Z."""
        return Vec3(float(col), 0.0, float(-row))

    def get_transform(self, block):
        """Tính toán transform chuẩn cho 4 trạng thái Orientation với mặt sàn tại y = 0.0."""
        ori = getattr(block, "orientation", Orientation.STANDING)

        # 1. Khối đứng (STANDING): 1x2x1 tại pos1, tâm y = 1.0
        if ori == Orientation.STANDING or (hasattr(ori, "name") and ori.name == "STANDING") or ori == 0:
            p1 = self.grid_to_world(block.pos1[0], block.pos1[1])
            pos = Vec3(p1.x, 1.0, p1.z)
            scale = Vec3(0.94, 2.0, 0.94)
            return BlockTransform(pos, scale)

        # 2. Khối nằm ngang (HORIZONTAL): 2x1x1 tại trung điểm pos1 và pos2, tâm y = 0.5
        elif ori == Orientation.HORIZONTAL or (hasattr(ori, "name") and ori.name == "HORIZONTAL") or ori == 1:
            p1 = self.grid_to_world(block.pos1[0], block.pos1[1])
            p2 = self.grid_to_world(block.pos2[0], block.pos2[1])
            center_x = (p1.x + p2.x) / 2.0
            center_z = (p1.z + p2.z) / 2.0
            pos = Vec3(center_x, 0.5, center_z)
            scale = Vec3(1.94, 1.0, 0.94)
            return BlockTransform(pos, scale)

        # 3. Khối nằm dọc (VERTICAL): 1x1x2 tại trung điểm pos1 và pos2, tâm y = 0.5
        elif ori == Orientation.VERTICAL or (hasattr(ori, "name") and ori.name == "VERTICAL") or ori == 2:
            p1 = self.grid_to_world(block.pos1[0], block.pos1[1])
            p2 = self.grid_to_world(block.pos2[0], block.pos2[1])
            center_x = (p1.x + p2.x) / 2.0
            center_z = (p1.z + p2.z) / 2.0
            pos = Vec3(center_x, 0.5, center_z)
            scale = Vec3(0.94, 1.0, 1.94)
            return BlockTransform(pos, scale)

        # 4. Hai cube tách rời (SPLIT): hai cube 1x1x1 tại pos1 và pos2, tâm y = 0.5
        else:
            p1 = self.grid_to_world(block.pos1[0], block.pos1[1])
            p2 = self.grid_to_world(block.pos2[0], block.pos2[1])
            active_idx = getattr(block, "active_index", 0)
            active_pos = p1 if active_idx == 0 else p2
            split_info = {
                "cube1_pos": Vec3(p1.x, 0.5, p1.z),
                "cube2_pos": Vec3(p2.x, 0.5, p2.z),
                "scale": Vec3(0.94, 1.0, 0.94),
                "active_index": active_idx,
            }
            return BlockTransform(Vec3(active_pos.x, 0.5, active_pos.z), Vec3(0.94, 1.0, 0.94), split_info=split_info)

    def stop_animations(self):
        """Dừng sạch mọi animation đang chạy trên các thực thể block."""
        for ent in (self.block_entity, self.split_cube1, self.split_cube2):
            if ent and hasattr(ent, "animations"):
                for anim in list(ent.animations):
                    try:
                        anim.kill()
                    except Exception:
                        pass
                ent.animations.clear()

    def update_transform(self):
        """Cập nhật vị trí, kích thước và màu sắc hiển thị của các thực thể 3D."""
        if not self.current_block:
            return

        self.stop_animations()

        ori = getattr(self.current_block, "orientation", Orientation.STANDING)
        is_split = (ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3)

        if is_split:
            # Ẩn khối chính, bật 2 cube con
            self.block_entity.enabled = False
            self.split_cube1.enabled = True
            self.split_cube2.enabled = True

            p1 = self.grid_to_world(self.current_block.pos1[0], self.current_block.pos1[1])
            p2 = self.grid_to_world(self.current_block.pos2[0], self.current_block.pos2[1])

            self.split_cube1.position = Vec3(p1.x, 0.5, p1.z)
            self.split_cube1.scale = Vec3(0.94, 1.0, 0.94)
            self.split_cube1.rotation = Vec3(0, 0, 0)

            self.split_cube2.position = Vec3(p2.x, 0.5, p2.z)
            self.split_cube2.scale = Vec3(0.94, 1.0, 0.94)
            self.split_cube2.rotation = Vec3(0, 0, 0)

            # Đổi màu cube active / inactive
            active_idx = getattr(self.current_block, "active_index", 0)
            if self.texture:
                col_active = color.rgb32(255, 240, 190)
                col_inactive = color.rgb32(130, 145, 165)
            else:
                col_active = ACTIVE_CUBE_COLOR
                col_inactive = INACTIVE_CUBE_COLOR

            if active_idx == 0:
                self.split_cube1.color = col_active
                self.split_cube2.color = col_inactive
            else:
                self.split_cube1.color = col_inactive
                self.split_cube2.color = col_active
        else:
            # Bật khối chính, ẩn 2 cube con
            self.split_cube1.enabled = False
            self.split_cube2.enabled = False
            self.block_entity.enabled = True

            transform = self.get_transform(self.current_block)
            self.block_entity.position = transform.position
            self.block_entity.scale = transform.scale
            self.block_entity.rotation = Vec3(0, 0, 0)
            if self.texture:
                self.block_entity.color = color.white
            else:
                self.block_entity.color = BLOCK_COLOR_STAND

    def get_pivot_data(self, block, direction):
        """Tính toán tọa độ pivot tại mép cạnh tiếp xúc sàn (y = 0.0), trục xoay và góc quay."""
        transform = self.get_transform(block)
        center = transform.position

        ori = getattr(block, "orientation", Orientation.STANDING)
        if ori == Orientation.STANDING or (hasattr(ori, "name") and ori.name == "STANDING") or ori == 0:
            cells_x = 1.0
            cells_z = 1.0
        elif ori == Orientation.HORIZONTAL or (hasattr(ori, "name") and ori.name == "HORIZONTAL") or ori == 1:
            cells_x = 2.0
            cells_z = 1.0
        elif ori == Orientation.VERTICAL or (hasattr(ori, "name") and ori.name == "VERTICAL") or ori == 2:
            cells_x = 1.0
            cells_z = 2.0
        else:
            cells_x = 1.0
            cells_z = 1.0

        half_x = cells_x / 2.0
        half_z = cells_z / 2.0

        dir_str = str(direction).upper()

        # Trong hệ Ursina Y-up, row giảm (UP) là +Z; row tăng (DOWN) là -Z;
        # col tăng (RIGHT) là +X; col giảm (LEFT) là -X.
        if dir_str == "UP":
            pivot_pos = Vec3(center.x, 0.0, center.z + half_z)
            axis = "x"
            angle = 90.0
        elif dir_str == "DOWN":
            pivot_pos = Vec3(center.x, 0.0, center.z - half_z)
            axis = "x"
            angle = -90.0
        elif dir_str == "RIGHT":
            pivot_pos = Vec3(center.x + half_x, 0.0, center.z)
            axis = "z"
            angle = 90.0
        elif dir_str == "LEFT":
            pivot_pos = Vec3(center.x - half_x, 0.0, center.z)
            axis = "z"
            angle = -90.0
        else:
            pivot_pos = Vec3(center.x, 0.0, center.z)
            axis = "x"
            angle = 0.0

        return pivot_pos, axis, angle

    def animate_move(self, old_block, new_block, direction, on_complete):
        """Diễn hoạt chuyển động lăn 3D cho khối bình thường hoặc chuyển nhánh split."""
        old_ori = getattr(old_block, "orientation", Orientation.STANDING)
        new_ori = getattr(new_block, "orientation", Orientation.STANDING)

        is_old_split = (old_ori == Orientation.SPLIT or (hasattr(old_ori, "name") and old_ori.name == "SPLIT") or old_ori == 3)
        is_new_split = (new_ori == Orientation.SPLIT or (hasattr(new_ori, "name") and new_ori.name == "SPLIT") or new_ori == 3)

        if is_old_split or str(direction).upper() == "SWITCH":
            self._animate_split_move(old_block, new_block, direction, on_complete)
            return

        # 1. Lăn khối liền chuẩn
        pivot_pos, axis, angle = self.get_pivot_data(old_block, direction)
        pivot = Entity(parent=self.root, position=pivot_pos)

        self.block_entity.world_parent = pivot

        duration = 0.16
        if axis == "x":
            pivot.animate_rotation_x(angle, duration=duration, curve=curve.linear)
        else:
            pivot.animate_rotation_z(angle, duration=duration, curve=curve.linear)

        invoke(lambda: self._finish_roll_animation(pivot, new_block, on_complete), delay=duration)

    def _finish_roll_animation(self, pivot, new_block, on_complete):
        """Dọn dẹp pivot sau khi lăn, đồng bộ transform chuẩn theo new_block."""
        if self.block_entity:
            self.block_entity.world_parent = self.root

        if pivot:
            destroy(pivot)

        self.current_block = new_block
        self.update_transform()

        # Nếu vừa chuyển từ khối liền sang split, thêm hiệu ứng nảy scale nhẹ cho 2 cube
        new_ori = getattr(new_block, "orientation", Orientation.STANDING)
        is_new_split = (new_ori == Orientation.SPLIT or (hasattr(new_ori, "name") and new_ori.name == "SPLIT") or new_ori == 3)
        if is_new_split:
            orig_scale = Vec3(0.94, 1.0, 0.94)
            self.split_cube1.scale = orig_scale * 1.25
            self.split_cube1.animate_scale(orig_scale, duration=0.15, curve=curve.out_sine)
            self.split_cube2.scale = orig_scale * 1.25
            self.split_cube2.animate_scale(orig_scale, duration=0.15, curve=curve.out_sine)

        if on_complete:
            on_complete()

    def _animate_split_move(self, old_block, new_block, direction, on_complete):
        """Diễn hoạt đổi cube active, di chuyển cube lẻ hoặc ghép lại thành khối liền."""
        dir_str = str(direction).upper()

        # Trường hợp 1: Hành động SWITCH
        if dir_str == "SWITCH":
            self.current_block = new_block
            self.update_transform()

            # Hiệu ứng nhịp nảy nhẹ báo hiệu cube active mới
            active_idx = getattr(new_block, "active_index", 0)
            active_cube = self.split_cube1 if active_idx == 0 else self.split_cube2
            orig_scale = Vec3(0.94, 1.0, 0.94)
            active_cube.scale = orig_scale * 1.18
            active_cube.animate_scale(orig_scale, duration=0.12, curve=curve.out_sine)

            invoke(lambda: on_complete() if on_complete else None, delay=0.13)
            return

        # Trường hợp 2: Lăn 1 cube lẻ trong trạng thái split
        active_idx = getattr(old_block, "active_index", 0)
        moved_entity = self.split_cube1 if active_idx == 0 else self.split_cube2
        cube_cell = old_block.pos1 if active_idx == 0 else old_block.pos2

        cube_world = self.grid_to_world(cube_cell[0], cube_cell[1])
        if dir_str == "UP":
            pivot_pos = Vec3(cube_world.x, 0.0, cube_world.z + 0.5)
            axis = "x"
            angle = 90.0
        elif dir_str == "DOWN":
            pivot_pos = Vec3(cube_world.x, 0.0, cube_world.z - 0.5)
            axis = "x"
            angle = -90.0
        elif dir_str == "RIGHT":
            pivot_pos = Vec3(cube_world.x + 0.5, 0.0, cube_world.z)
            axis = "z"
            angle = 90.0
        elif dir_str == "LEFT":
            pivot_pos = Vec3(cube_world.x - 0.5, 0.0, cube_world.z)
            axis = "z"
            angle = -90.0
        else:
            pivot_pos = Vec3(cube_world.x, 0.0, cube_world.z)
            axis = "x"
            angle = 0.0

        pivot = Entity(parent=self.root, position=pivot_pos)
        moved_entity.world_parent = pivot

        self._split_pivot = pivot
        self._split_moved_entity = moved_entity

        duration = 0.16
        if axis == "x":
            pivot.animate_rotation_x(angle, duration=duration, curve=curve.linear)
        else:
            pivot.animate_rotation_z(angle, duration=duration, curve=curve.linear)

        invoke(lambda: self._finish_split_animation(new_block, on_complete), delay=duration)

    def _finish_split_animation(self, new_block, on_complete):
        """Hoàn tất animation split hoặc chuyển hóa ghép khối."""
        if hasattr(self, "_split_moved_entity") and self._split_moved_entity:
            self._split_moved_entity.world_parent = self.root
            self._split_moved_entity = None

        if hasattr(self, "_split_pivot") and self._split_pivot:
            destroy(self._split_pivot)
            self._split_pivot = None

        self.current_block = new_block
        self.update_transform()

        if on_complete:
            on_complete()

    def animate_goal_fall(self, on_complete):
        """Diễn hoạt khối chìm dần vào lòng ô goal và biến mất khi vào trong ô (không lòi xuống dưới đáy map)."""
        duration = 0.65
        ori = getattr(self.current_block, "orientation", Orientation.STANDING)
        is_split = (ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3)

        target = (self.split_cube1 if getattr(self.current_block, "active_index", 0) == 0 else self.split_cube2) if is_split else self.block_entity

        # Đáy khối luôn giữ ở y = 0.0 (mặt sàn miệng hố), chiều cao và tâm khối hạ dần về 0
        # Tạo hiệu ứng khối chìm lọt vào trong lòng ô goal và biến mất sạch sẽ, không bị lòi xuống dưới sàn map
        target.animate_y(0.0, duration=duration, curve=curve.in_quad)
        target.animate_scale_y(0.0, duration=duration, curve=curve.in_quad)
        target.animate_color(color.rgba32(0, 0, 0, 0), duration=duration, curve=curve.in_quad)

        def _cleanup():
            if target:
                target.enabled = False
            if on_complete:
                on_complete()

        invoke(_cleanup, delay=duration + 0.05)

    def animate_fall(self, on_complete, rotate=True, distance=18.0):
        """Diễn hoạt rơi thẳng đứng xuống vực sâu khi đứng trên ô rỗng/ô nứt sập."""
        duration = 0.75
        ori = getattr(self.current_block, "orientation", Orientation.STANDING)
        is_split = (ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3)

        if is_split:
            active_idx = getattr(self.current_block, "active_index", 0)
            active_cube = self.split_cube1 if active_idx == 0 else self.split_cube2
            active_cube.animate_y(active_cube.y - distance, duration=duration, curve=curve.in_quad)
            active_cube.animate_scale(Vec3(0.01, 0.01, 0.01), duration=duration, curve=curve.in_quad)
            active_cube.animate_color(color.rgba32(0, 0, 0, 0), duration=duration, curve=curve.in_quad)
            if rotate:
                active_cube.animate_rotation_x(active_cube.rotation_x + 40, duration=duration)

            def _cleanup_split():
                active_cube.enabled = False
                if on_complete:
                    on_complete()

            invoke(_cleanup_split, delay=duration + 0.05)
        else:
            self.block_entity.animate_y(self.block_entity.y - distance, duration=duration, curve=curve.in_quad)
            self.block_entity.animate_scale(Vec3(0.01, 0.01, 0.01), duration=duration, curve=curve.in_quad)
            self.block_entity.animate_color(color.rgba32(0, 0, 0, 0), duration=duration, curve=curve.in_quad)
            if rotate:
                self.block_entity.animate_rotation_x(self.block_entity.rotation_x + 35, duration=duration)

            def _cleanup_block():
                if self.block_entity:
                    self.block_entity.enabled = False
                if on_complete:
                    on_complete()

            invoke(_cleanup_block, delay=duration + 0.05)

    def animate_split_fall(self, supported_cells, on_complete):
        """Diễn hoạt rơi cho các cube bị mất sàn đỡ trong trạng thái split."""
        duration = 0.75
        pos1 = getattr(self.current_block, "pos1", None)
        pos2 = getattr(self.current_block, "pos2", None)

        fall_1 = pos1 not in supported_cells if pos1 else True
        fall_2 = pos2 not in supported_cells if pos2 else True

        if not fall_1 and not fall_2:
            fall_1 = True

        if fall_1:
            self.split_cube1.animate_y(self.split_cube1.y - 18.0, duration=duration, curve=curve.in_quad)
            self.split_cube1.animate_scale(Vec3(0.01, 0.01, 0.01), duration=duration, curve=curve.in_quad)
            self.split_cube1.animate_color(color.rgba32(0, 0, 0, 0), duration=duration, curve=curve.in_quad)
            self.split_cube1.animate_rotation_z(self.split_cube1.rotation_z + 30, duration=duration)

        if fall_2:
            self.split_cube2.animate_y(self.split_cube2.y - 18.0, duration=duration, curve=curve.in_quad)
            self.split_cube2.animate_scale(Vec3(0.01, 0.01, 0.01), duration=duration, curve=curve.in_quad)
            self.split_cube2.animate_color(color.rgba32(0, 0, 0, 0), duration=duration, curve=curve.in_quad)
            self.split_cube2.animate_rotation_z(self.split_cube2.rotation_z - 30, duration=duration)

        def _cleanup():
            if fall_1:
                self.split_cube1.enabled = False
            if fall_2:
                self.split_cube2.enabled = False
            if on_complete:
                on_complete()

        invoke(_cleanup, delay=duration + 0.05)

    def animate_tip_and_fall(self, invalid_block, direction, on_complete):
        """Diễn hoạt khối nghiêng qua mép bàn cờ khi lăn trượt ra ngoài rồi rơi tự do."""
        ori = getattr(self.current_block, "orientation", Orientation.STANDING)
        is_split = (ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3)

        if is_split:
            active_idx = getattr(self.current_block, "active_index", 0)
            active_cell = self.current_block.pos1 if active_idx == 0 else self.current_block.pos2
            cube_world = self.grid_to_world(active_cell[0], active_cell[1])
            dir_str = str(direction).upper()

            if dir_str == "UP":
                pivot_pos = Vec3(cube_world.x, 0.0, cube_world.z + 0.5)
                axis = "x"
                angle = 90.0
            elif dir_str == "DOWN":
                pivot_pos = Vec3(cube_world.x, 0.0, cube_world.z - 0.5)
                axis = "x"
                angle = -90.0
            elif dir_str == "RIGHT":
                pivot_pos = Vec3(cube_world.x + 0.5, 0.0, cube_world.z)
                axis = "z"
                angle = 90.0
            elif dir_str == "LEFT":
                pivot_pos = Vec3(cube_world.x - 0.5, 0.0, cube_world.z)
                axis = "z"
                angle = -90.0
            else:
                pivot_pos = Vec3(cube_world.x, 0.0, cube_world.z)
                axis = "x"
                angle = 0.0
        else:
            pivot_pos, axis, angle = self.get_pivot_data(self.current_block, direction)

        self._tip_from_pivot(pivot_pos, axis, angle, on_complete)

    def animate_edge_tip_and_fall(self, supported_cell, direction, on_complete):
        """Diễn hoạt khối nằm nghiêng sụp xuống mép ô đỡ khi nửa kia lơ lửng ngoài vực."""
        sup_pos = self.grid_to_world(supported_cell[0], supported_cell[1])
        dir_str = str(direction).upper()

        if dir_str == "UP":
            pivot_pos = Vec3(sup_pos.x, 0.0, sup_pos.z + 0.5)
            axis = "x"
            angle = 90.0
        elif dir_str == "DOWN":
            pivot_pos = Vec3(sup_pos.x, 0.0, sup_pos.z - 0.5)
            axis = "x"
            angle = -90.0
        elif dir_str == "RIGHT":
            pivot_pos = Vec3(sup_pos.x + 0.5, 0.0, sup_pos.z)
            axis = "z"
            angle = 90.0
        elif dir_str == "LEFT":
            pivot_pos = Vec3(sup_pos.x - 0.5, 0.0, sup_pos.z)
            axis = "z"
            angle = -90.0
        else:
            pivot_pos = Vec3(sup_pos.x, 0.0, sup_pos.z)
            axis = "x"
            angle = 0.0

        self._tip_from_pivot(pivot_pos, axis, angle, on_complete)

    def _tip_from_pivot(self, pivot_position, axis, angle, on_complete):
        """Nghiêng khối quanh cạnh sàn pivot trước khi rơi."""
        ori = getattr(self.current_block, "orientation", Orientation.STANDING)
        is_split = (ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3)

        if is_split:
            active_idx = getattr(self.current_block, "active_index", 0)
            target_entity = self.split_cube1 if active_idx == 0 else self.split_cube2
        else:
            target_entity = self.block_entity

        pivot = Entity(parent=self.root, position=pivot_position)
        target_entity.world_parent = pivot
        self._tipping_entity = target_entity

        tip_duration = 0.22
        if axis == "x":
            pivot.animate_rotation_x(angle, duration=tip_duration, curve=curve.in_quad)
        else:
            pivot.animate_rotation_z(angle, duration=tip_duration, curve=curve.in_quad)

        invoke(lambda: self._finish_tip(pivot, 0.60, on_complete), delay=tip_duration)

    def _finish_tip(self, pivot, fall_duration, on_complete):
        """Tiếp tục rơi thẳng đứng xuống vực sau khi đã nghiêng qua mép."""
        pivot.animate_y(pivot.y - 18.0, duration=fall_duration, curve=curve.in_quad)
        pivot.animate_scale(Vec3(0.01, 0.01, 0.01), duration=fall_duration, curve=curve.in_quad)

        tipping_entity = getattr(self, "_tipping_entity", None)
        target = tipping_entity if tipping_entity else self.block_entity
        if target:
            target.animate_color(color.rgba32(0, 0, 0, 0), duration=fall_duration, curve=curve.in_quad)

        def _cleanup():
            tipping_entity = getattr(self, "_tipping_entity", None)
            if tipping_entity:
                tipping_entity.world_parent = self.root
                tipping_entity.enabled = False
                self._tipping_entity = None
            elif self.block_entity:
                self.block_entity.world_parent = self.root
                self.block_entity.enabled = False

            if pivot:
                destroy(pivot)
            if on_complete:
                on_complete()

        invoke(_cleanup, delay=fall_duration + 0.05)
