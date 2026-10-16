"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class Game:

    def __init__(self, level_path, mode='play', algorithm=None, on_back=None, audio_manager=None):
        raise NotImplementedError

    def start_solver(self):
        raise NotImplementedError

    def play_next_solution_move(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def input(self, key):
        raise NotImplementedError

    def try_move(self, action):
        raise NotImplementedError

    def finish_move(self, transition):
        raise NotImplementedError

    def start_fall(self, transition, direction):
        raise NotImplementedError

    def create_ui(self):
        raise NotImplementedError

    def create_result_panel(self):
        raise NotImplementedError

    def _set_result_texts(self, title, subtitle, stats, title_color, stats_scale):
        raise NotImplementedError

    def show_win(self):
        raise NotImplementedError

    def show_lose(self):
        raise NotImplementedError

    def show_no_solution(self):
        raise NotImplementedError

    def show_solver_error(self, message):
        raise NotImplementedError

    def _show_result(self, title, subtitle, stats, outcome, detailed=False, show_cube=True):
        raise NotImplementedError

    def back_to_level_select(self):
        raise NotImplementedError

    def restart(self):
        raise NotImplementedError

    def on_destroy(self):
        raise NotImplementedError
