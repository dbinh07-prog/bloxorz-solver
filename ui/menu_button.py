"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""


class _MenuHitbox:

    def __init__(self, owner, **kwargs):
        raise NotImplementedError

    def on_mouse_enter(self):
        raise NotImplementedError

    def on_mouse_exit(self):
        raise NotImplementedError

    def input(self, key):
        raise NotImplementedError

class MenuTextButton:

    def __init__(self, text, position=None, font=None, on_click=None, text_scale=1.8, main_color=None, glow_rgb=None, glow_rings=None, parent=None, hitbox_width=None, hitbox_origin=None, label_origin=None):
        raise NotImplementedError

    def _on_hover_enter(self):
        raise NotImplementedError

    def _on_hover_exit(self):
        raise NotImplementedError

    def _on_press_down(self):
        raise NotImplementedError

    def _on_press_up(self):
        raise NotImplementedError
