from pathlib import Path
from ursina import Entity, Text, color


def _build_color(rgb_tuple, alpha_val):
    r, g, b = rgb_tuple
    a = max(0, min(255, int(alpha_val)))
    return color.rgba32(int(r), int(g), int(b), a)


_DEFAULT_8_DIRECTIONS = (
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7),
)


class GlowText(Entity):

    def __init__(
        self,
        text,
        font=None,
        origin=None,
        main_color=None,
        glow_rgb=None,
        rings=None,
        directions=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._label = text
        self._origin = origin if origin is not None else (-0.5, 0)

        if font and not Path(str(font)).exists():
            self._font = None
        else:
            self._font = font

        self._main_color = main_color if main_color is not None else color.rgb32(240, 250, 255)
        self._glow_rgb = glow_rgb if glow_rgb is not None else (0, 195, 255)
        self._rings = rings or ()
        self._directions = directions if directions is not None else _DEFAULT_8_DIRECTIONS

        self._glow_labels = []
        self._glow_base_alphas = []

        font_kwargs = {"font": self._font} if self._font else {}
        for ring_offset, alpha in self._rings:
            for dx, dy in self._directions:
                glow_col = _build_color(self._glow_rgb, alpha)
                lbl = Text(
                    parent=self,
                    text=text,
                    origin=self._origin,
                    position=(dx * ring_offset, dy * ring_offset, 0.01),
                    color=glow_col,
                    **font_kwargs,
                )
                self._glow_labels.append(lbl)
                self._glow_base_alphas.append(alpha)

        self.main_label = Text(
            parent=self,
            text=text,
            origin=self._origin,
            position=(0, 0, 0),
            color=self._main_color,
            **font_kwargs,
        )

    @property
    def text(self):
        return self.main_label.text

    @text.setter
    def text(self, value):
        self._label = value
        self.main_label.text = value
        for lbl in self._glow_labels:
            lbl.text = value

    def set_main_color(self, new_color):
        self._main_color = new_color
        self.main_label.color = new_color

    def set_glow_alpha_scale(self, factor):
        for lbl, base_alpha in zip(self._glow_labels, self._glow_base_alphas):
            new_alpha = max(0, min(255, int(base_alpha * factor)))
            lbl.color = _build_color(self._glow_rgb, new_alpha)
