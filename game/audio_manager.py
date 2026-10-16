"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class AudioManager:

    def __init__(self, parent=None):
        raise NotImplementedError

    def play_move_sound(self):
        raise NotImplementedError

    def play_win_sound(self):
        raise NotImplementedError

    def play_lose_sound(self):
        raise NotImplementedError

    def stop_result_sounds(self):
        raise NotImplementedError

    def _apply_music_volume(self):
        raise NotImplementedError

    def duck_music(self):
        raise NotImplementedError

    def restore_music(self):
        raise NotImplementedError

    def set_music_volume(self, volume):
        raise NotImplementedError

    def set_sfx_volume(self, volume):
        raise NotImplementedError

    def toggle_music(self):
        raise NotImplementedError
