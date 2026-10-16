"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class Renderer:

    def __init__(self, board, parent):
        raise NotImplementedError

    def check_textures(self):
        raise NotImplementedError

    def grid_to_world(self, row, col):
        raise NotImplementedError

    def get_tile_texture(self, tile_type):
        raise NotImplementedError

    def create_map(self):
        raise NotImplementedError

    def refresh_bridge_states(self, bridge_states):
        raise NotImplementedError
