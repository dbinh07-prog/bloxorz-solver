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

BLOCK_TEXTURE_PATH = "assets/texture/Block.jpg"

BLOCK_COLOR_STAND = color.rgb32(245, 158, 11)
ACTIVE_CUBE_COLOR = color.rgb32(0, 225, 255)
INACTIVE_CUBE_COLOR = color.rgb32(30, 80, 130)


class BlockTransform:

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
        self._pending_callbacks = []
        self._animation_session = 0

        self.root = Entity(parent=parent)

        self.texture = None
        candidates = [BLOCK_TEXTURE_PATH, "assets/texture/Block.jpg", "assets/texture/block.jpg", "assets/texture/block.png"]
        for cand in candidates:
            if cand and Path(cand).exists():
                self.texture = cand
                break

        self.block_entity = Entity(
            parent=self.root,
            model="cube",
            texture=self.texture,
            color=color.white if self.texture else BLOCK_COLOR_STAND,
        )

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
        return Vec3(float(col), 0.0, float(-row))

    def get_transform(self, block):
        ori = getattr(block, "orientation", Orientation.STANDING)

        if ori == Orientation.STANDING or (hasattr(ori, "name") and ori.name == "STANDING") or ori == 0:
            p1 = self.grid_to_world(block.pos1[0], block.pos1[1])
            pos = Vec3(p1.x, 1.0, p1.z)
            scale = Vec3(0.94, 2.0, 0.94)
            return BlockTransform(pos, scale)

        elif ori == Orientation.HORIZONTAL or (hasattr(ori, "name") and ori.name == "HORIZONTAL") or ori == 1:
            p1 = self.grid_to_world(block.pos1[0], block.pos1[1])
            p2 = self.grid_to_world(block.pos2[0], block.pos2[1])
            center_x = (p1.x + p2.x) / 2.0
            center_z = (p1.z + p2.z) / 2.0
            pos = Vec3(center_x, 0.5, center_z)
            scale = Vec3(1.94, 1.0, 0.94)
            return BlockTransform(pos, scale)

        elif ori == Orientation.VERTICAL or (hasattr(ori, "name") and ori.name == "VERTICAL") or ori == 2:
            p1 = self.grid_to_world(block.pos1[0], block.pos1[1])
            p2 = self.grid_to_world(block.pos2[0], block.pos2[1])
            center_x = (p1.x + p2.x) / 2.0
            center_z = (p1.z + p2.z) / 2.0
            pos = Vec3(center_x, 0.5, center_z)
            scale = Vec3(0.94, 1.0, 1.94)
            return BlockTransform(pos, scale)

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

    def _later(self, callback, delay):
        session = self._animation_session
        pending = None

        def finish():
            if pending in self._pending_callbacks:
                self._pending_callbacks.remove(pending)
            if session == self._animation_session:
                callback()

        pending = invoke(finish, delay=delay)
        self._pending_callbacks.append(pending)

    def stop_animations(self):
        self._animation_session += 1
        for pending in self._pending_callbacks:
            pending.kill()
        self._pending_callbacks.clear()
        for pivot in list(self.root.children):
            if pivot not in (self.block_entity, self.split_cube1, self.split_cube2):
                for cube in (self.block_entity, self.split_cube1, self.split_cube2):
                    if cube.parent == pivot:
                        cube.world_parent = self.root
                destroy(pivot)
        self._split_pivot = None
        self._split_moved_entity = None
        for ent in (self.block_entity, self.split_cube1, self.split_cube2):
            if ent and hasattr(ent, "animations"):
                for anim in list(ent.animations):
                    try:
                        anim.kill()
                    except Exception:
                        pass
                ent.animations.clear()

    def update_transform(self):
        if not self.current_block:
            return

        self.stop_animations()

        ori = getattr(self.current_block, "orientation", Orientation.STANDING)
        is_split = (ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3)

        if is_split:
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
        old_ori = getattr(old_block, "orientation", Orientation.STANDING)
        new_ori = getattr(new_block, "orientation", Orientation.STANDING)

        is_old_split = (old_ori == Orientation.SPLIT or (hasattr(old_ori, "name") and old_ori.name == "SPLIT") or old_ori == 3)
        is_new_split = (new_ori == Orientation.SPLIT or (hasattr(new_ori, "name") and new_ori.name == "SPLIT") or new_ori == 3)

        if is_old_split or str(direction).upper() == "SWITCH":
            self._animate_split_move(old_block, new_block, direction, on_complete)
            return

        pivot_pos, axis, angle = self.get_pivot_data(old_block, direction)
        pivot = Entity(parent=self.root, position=pivot_pos)

        self.block_entity.world_parent = pivot

        duration = 0.16
        if axis == "x":
            pivot.animate_rotation_x(angle, duration=duration, curve=curve.linear)
        else:
            pivot.animate_rotation_z(angle, duration=duration, curve=curve.linear)

        self._later(lambda: self._finish_roll_animation(pivot, new_block, on_complete), delay=duration)

    def _finish_roll_animation(self, pivot, new_block, on_complete):
        if self.block_entity:
            self.block_entity.world_parent = self.root

        if pivot:
            destroy(pivot)

        self.current_block = new_block
        self.update_transform()

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
        dir_str = str(direction).upper()

        if dir_str == "SWITCH":
            self.current_block = new_block
            self.update_transform()

            active_idx = getattr(new_block, "active_index", 0)
            active_cube = self.split_cube1 if active_idx == 0 else self.split_cube2
            orig_scale = Vec3(0.94, 1.0, 0.94)
            active_cube.scale = orig_scale * 1.18
            active_cube.animate_scale(orig_scale, duration=0.12, curve=curve.out_sine)

            self._later(lambda: on_complete() if on_complete else None, delay=0.13)
            return

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

        self._later(lambda: self._finish_split_animation(new_block, on_complete), delay=duration)

    def _finish_split_animation(self, new_block, on_complete):
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
        duration = 0.65
        ori = getattr(self.current_block, "orientation", Orientation.STANDING)
        is_split = (ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3)

        target = (self.split_cube1 if getattr(self.current_block, "active_index", 0) == 0 else self.split_cube2) if is_split else self.block_entity

        target.animate_y(0.0, duration=duration, curve=curve.in_quad)
        target.animate_scale_y(0.0, duration=duration, curve=curve.in_quad)
        target.animate_color(color.rgba32(0, 0, 0, 0), duration=duration, curve=curve.in_quad)

        def _cleanup():
            if target:
                target.enabled = False
            if on_complete:
                on_complete()

        self._later(_cleanup, delay=duration + 0.05)

    def animate_fall(self, on_complete, rotate=True, distance=18.0):
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

            self._later(_cleanup_split, delay=duration + 0.05)
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

            self._later(_cleanup_block, delay=duration + 0.05)

    def animate_split_fall(self, supported_cells, on_complete):
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

        self._later(_cleanup, delay=duration + 0.05)

    def animate_tip_and_fall(self, invalid_block, direction, on_complete):
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

        self._later(lambda: self._finish_tip(pivot, 0.60, on_complete), delay=tip_duration)

    def _finish_tip(self, pivot, fall_duration, on_complete):
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

        self._later(_cleanup, delay=fall_duration + 0.05)
