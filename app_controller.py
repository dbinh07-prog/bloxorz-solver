"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class AppController:

    def __init__(self):
        raise NotImplementedError

    def input(self, key):
        raise NotImplementedError

    def clear_screen(self):
        raise NotImplementedError

    def show_main_menu(self):
        raise NotImplementedError

    def show_tutorial(self):
        raise NotImplementedError

    def show_level_select(self, mode):
        raise NotImplementedError

    def handle_level_selected(self, level_path, mode, algorithm=None):
        raise NotImplementedError

    def start_game(self, level_path, mode, algorithm):
        raise NotImplementedError
