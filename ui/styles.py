"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""

from ursina import Button, color
from ursina.models.procedural.quad import Quad

from ui.theme import (
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
    PRIMARY,
    PRIMARY_HOVER,
    WHITE,
    DARK_PANEL,
)
from ui.ui_sound import get_click_audio, get_hover_audio


class MenuButton(Button):

    def __init__(self, text='', **kwargs):
        options = dict(
            text=text,
            model=Quad(radius=0.08, aspect=BUTTON_WIDTH / BUTTON_HEIGHT),
            scale=(BUTTON_WIDTH, BUTTON_HEIGHT),
            color=DARK_PANEL,
            highlight_color=PRIMARY_HOVER or PRIMARY,
            pressed_color=color.rgb32(20, 32, 50),
            text_color=WHITE,
            text_size=1.15,
            highlight_scale=1.05,
            pressed_scale=0.95,
            highlight_sound=get_hover_audio(),
            pressed_sound=get_click_audio(),
        )
        options.update(kwargs)
        super().__init__(**options)
