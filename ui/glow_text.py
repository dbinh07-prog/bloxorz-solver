"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class GlowText:

    def __init__(self, text, font=None, origin=None, main_color=None, glow_rgb=None, rings=None, directions=None, **kwargs):
        raise NotImplementedError

    @property
    def text(self):
        raise NotImplementedError

    @text.setter
    def text(self, value):
        raise NotImplementedError

    def set_main_color(self, new_color):
        raise NotImplementedError

    def set_glow_alpha_scale(self, factor):
        raise NotImplementedError
