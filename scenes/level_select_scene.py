"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


def get_level_number(path):
    raise NotImplementedError

class LevelSelectScene:

    def __init__(self, mode, on_level_selected, on_back):
        raise NotImplementedError

    def get_level_files(self):
        raise NotImplementedError

    def create_level_buttons(self):
        raise NotImplementedError

    def select_level(self, level_path):
        raise NotImplementedError

    def open_algorithm_panel(self, level_path):
        raise NotImplementedError

    def select_algorithm(self, algorithm):
        raise NotImplementedError

    def close_algorithm_panel(self):
        raise NotImplementedError

    def on_destroy(self):
        raise NotImplementedError
