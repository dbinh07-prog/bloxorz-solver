from pathlib import Path
from ursina import Button, Entity, Text, color, curve, invoke

from ui.glow_text import GlowText
from ui.theme import (
    FONT_REGULAR,
    GLOW_TEXT_COLOR,
    GLOW_HALO_RGB,
    MENU_ITEM_GLOW_RINGS,
    MENU_ITEM_HITBOX_HEIGHT,
    MENU_ITEM_HITBOX_CHAR_WIDTH,
    MENU_ITEM_HITBOX_MIN_WIDTH,
    MENU_INDICATOR_COLOR_IDLE,
    MENU_INDICATOR_COLOR_HOVER,
    HOVER_SCALE,
    PRESS_SCALE,
    HOVER_ANIM_DURATION,
    PRESS_ANIM_DURATION,
    RELEASE_ANIM_DURATION,
)
from ui.ui_sound import play_click, play_hover


class _MenuHitbox(Button):

    def __init__(self, owner, **kwargs):
        super().__init__(
            text="",
            model="quad",
            color=color.clear,
            highlight_color=color.clear,
            pressed_color=color.clear,
            **kwargs,
        )
        self.owner = owner

    def on_mouse_enter(self):
        self.owner._on_hover_enter()

    def on_mouse_exit(self):
        self.owner._on_hover_exit()

    def input(self, key):
        if self.hovered and key == "left mouse down":
            self.owner._on_press_down()

        if key == "left mouse up" and self.owner._is_pressed:
            if self.hovered:
                self.owner._on_press_up()
            else:
                self.owner._is_pressed = False
                self.owner._on_hover_exit()


class MenuTextButton(Entity):

    def __init__(
        self,
        text,
        position=None,
        font=None,
        on_click=None,
        text_scale=1.8,
        main_color=None,
        glow_rgb=None,
        glow_rings=None,
        parent=None,
        hitbox_width=None,
        hitbox_origin=None,
        label_origin=None,
    ):
        pos = position if position is not None else (0, 0)
        super().__init__(parent=parent, position=pos)

        self.callback = on_click
        self.text_scale = text_scale
        self._is_pressed = False

        h_origin = hitbox_origin if hitbox_origin is not None else (-0.5, 0)
        lbl_origin = label_origin if label_origin is not None else (-0.5, 0)

        resolved_font = font or FONT_REGULAR
        if resolved_font and not Path(str(resolved_font)).exists():
            resolved_font = None

        self.show_indicator = (lbl_origin == (-0.5, 0))

        font_kwargs = {"font": resolved_font} if resolved_font else {}
        self.indicator = Text(
            text=">",
            parent=self,
            origin=(-0.5, 0),
            position=(-0.09, 0, -0.02),
            scale=text_scale,
            color=MENU_INDICATOR_COLOR_IDLE,
            enabled=self.show_indicator,
            **font_kwargs,
        )

        self.label = GlowText(
            text=text,
            font=resolved_font,
            parent=self,
            origin=lbl_origin,
            main_color=main_color or GLOW_TEXT_COLOR,
            glow_rgb=glow_rgb or GLOW_HALO_RGB,
            rings=glow_rings or MENU_ITEM_GLOW_RINGS,
            scale=text_scale,
            position=(0, 0, -0.01),
        )

        if hitbox_width is None:
            hitbox_width = max(
                MENU_ITEM_HITBOX_MIN_WIDTH,
                len(text) * MENU_ITEM_HITBOX_CHAR_WIDTH * text_scale,
            )

        hitbox_x_offset = -0.02 if h_origin == (-0.5, 0) else 0

        self._hitbox = _MenuHitbox(
            owner=self,
            parent=self,
            origin=h_origin,
            scale=(hitbox_width, MENU_ITEM_HITBOX_HEIGHT * text_scale),
            position=(hitbox_x_offset, 0, 0.01),
        )

    def _on_hover_enter(self):
        self.label.animate_scale(
            self.text_scale * HOVER_SCALE,
            duration=HOVER_ANIM_DURATION,
            curve=curve.out_quad,
        )
        self.label.animate_x(0.018, duration=HOVER_ANIM_DURATION, curve=curve.out_quad)
        self.label.set_glow_alpha_scale(1.6)
        if self.indicator:
            self.indicator.animate_color(
                MENU_INDICATOR_COLOR_HOVER,
                duration=HOVER_ANIM_DURATION,
            )
        play_hover()

    def _on_hover_exit(self):
        if self._is_pressed:
            return

        self.label.animate_scale(
            self.text_scale,
            duration=HOVER_ANIM_DURATION,
            curve=curve.out_quad,
        )
        self.label.animate_x(0.0, duration=HOVER_ANIM_DURATION, curve=curve.out_quad)
        self.label.set_glow_alpha_scale(1.0)
        if self.indicator:
            self.indicator.animate_color(
                MENU_INDICATOR_COLOR_IDLE,
                duration=HOVER_ANIM_DURATION,
            )

    def _on_press_down(self):
        self._is_pressed = True

        self.label.animate_scale(
            self.text_scale * PRESS_SCALE,
            duration=PRESS_ANIM_DURATION,
        )

    def _on_press_up(self):
        self._is_pressed = False

        self.label.animate_scale(
            self.text_scale * HOVER_SCALE,
            duration=RELEASE_ANIM_DURATION,
            curve=curve.out_back,
        )
        self.label.animate_x(0.018, duration=RELEASE_ANIM_DURATION)

        play_click()

        if self.callback:
            invoke(self.callback, delay=RELEASE_ANIM_DURATION)
