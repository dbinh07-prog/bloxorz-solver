"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class BlockRenderer:

    def __init__(self, block_logic, parent):
        raise NotImplementedError

    def grid_to_world(self, row, col):
        raise NotImplementedError

    def get_transform(self, block):
        raise NotImplementedError

    def update_transform(self):
        raise NotImplementedError

    def get_pivot_data(self, block, direction):
        raise NotImplementedError

    def animate_move(self, old_block, new_block, direction, on_complete):
        raise NotImplementedError

    def _finish_roll_animation(self, pivot, new_block, on_complete):
        raise NotImplementedError

    def _animate_split_move(self, old_block, new_block, direction, on_complete):
        raise NotImplementedError

    def _finish_split_animation(self, new_block, on_complete):
        raise NotImplementedError

    def animate_fall(self, on_complete):
        raise NotImplementedError

    def animate_split_fall(self, supported_cells, on_complete):
        raise NotImplementedError

    def animate_tip_and_fall(self, invalid_block, direction, on_complete):
        raise NotImplementedError

    def animate_edge_tip_and_fall(self, supported_cell, direction, on_complete):
        raise NotImplementedError

    def _tip_from_pivot(self, pivot_position, axis, angle, on_complete):
        raise NotImplementedError

    def _finish_tip(self, pivot, fall_duration, on_complete):
        raise NotImplementedError
