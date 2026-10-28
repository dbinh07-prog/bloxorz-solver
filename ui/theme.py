from pathlib import Path
from ursina import color


_TITLE_FONT = "assets/fonts/PressStart2P-Regular.ttf"
FONT_TITLE = _TITLE_FONT if Path(_TITLE_FONT).exists() else None

_REGULAR_FONT = "assets/fonts/Orbitron-Bold.ttf"
FONT_REGULAR = _REGULAR_FONT if Path(_REGULAR_FONT).exists() else None

_BOLD_FONT = "assets/fonts/Orbitron-Bold.ttf"
FONT_BOLD = _BOLD_FONT if Path(_BOLD_FONT).exists() else None


BACKGROUND = color.rgb32(10, 14, 24)
PRIMARY = color.rgb32(0, 210, 255)
PRIMARY_HOVER = color.rgb32(90, 235, 255)
WHITE = color.rgb32(242, 246, 252)
GRAY = color.rgb32(148, 163, 184)
DARK_PANEL = color.rgba32(12, 18, 30, 210)
TRANSPARENT = color.rgba32(0, 0, 0, 0)

GLOW_TEXT_COLOR = color.rgb32(240, 250, 255)
GLOW_HALO_RGB = (0, 195, 255)
TITLE_GLOW_RINGS = ((0.003, 60), (0.008, 20))
MENU_ITEM_GLOW_RINGS = ((0.0025, 45),)

TITLE_SCALE = 2.5
SUBTITLE_SCALE = 0.95
MENU_ITEM_SCALE = 1.75
FOOTER_SCALE = 0.75

BUTTON_WIDTH = 0.36
BUTTON_HEIGHT = 0.075
MENU_ITEM_SPACING = 0.145
MENU_ITEM_HITBOX_HEIGHT = 0.12
MENU_ITEM_HITBOX_CHAR_WIDTH = 0.048
MENU_ITEM_HITBOX_MIN_WIDTH = 0.30

MENU_INDICATOR_COLOR_IDLE = color.rgba32(0, 195, 255, 0)
MENU_INDICATOR_COLOR_HOVER = color.rgb32(0, 225, 255)


FADE_TIME = 0.32
HOVER_SCALE = 1.06
PRESS_SCALE = 0.94
HOVER_ANIM_DURATION = 0.12
PRESS_ANIM_DURATION = 0.06
RELEASE_ANIM_DURATION = 0.08


def _pick_sound(candidates, default_path):
    for p in candidates:
        if p and Path(p).exists():
            return p
    return default_path


UI_CLICK_SOUND = _pick_sound(
    ["assets/sounds/click.mp3", "assets/sounds/ui_click.wav", "assets/sounds/click.wav", "assets/sounds/ui_click.mp3", "assets/sounds/block_land2.wav"],
    "assets/sounds/click.mp3",
)

UI_HOVER_SOUND = _pick_sound(
    ["assets/sounds/Hover.mp3", "assets/sounds/hover.mp3", "assets/sounds/ui_hover.wav", "assets/sounds/hover.wav", "assets/sounds/ui_hover.mp3", "assets/sounds/block_land2.wav"],
    "assets/sounds/Hover.mp3",
)

UI_CLICK_VOLUME = 1.0
UI_HOVER_VOLUME = 0.95

WIN_SOUND = _pick_sound(
    ["assets/sounds/Win.mp3", "assets/sounds/win.mp3", "assets/sounds/win.wav", "assets/sounds/victory.wav", "assets/sounds/block_land.wav"],
    "assets/sounds/Win.mp3",
)

LOSE_SOUND = _pick_sound(
    ["assets/sounds/Lose.mp3", "assets/sounds/lose.mp3", "assets/sounds/lose.wav", "assets/sounds/lost.wav", "assets/sounds/block_land.wav"],
    "assets/sounds/Lose.mp3",
)

WIN_SOUND_VOLUME = 0.85
LOSE_SOUND_VOLUME = 0.80
MUSIC_DUCK_VOLUME = 0.12


RESULT_PANEL_SCALE = (0.88, 0.78)
RESULT_PANEL_TINT_WIN = color.rgba32(12, 28, 22, 242)
RESULT_PANEL_TINT_LOSE = color.rgba32(32, 14, 18, 242)
RESULT_PANEL_TINT_NEUTRAL = color.rgba32(15, 20, 32, 242)

RESULT_TITLE_COLOR_WIN = color.rgb32(74, 222, 128)
RESULT_TITLE_COLOR_LOSE = color.rgb32(248, 113, 113)
RESULT_TITLE_COLOR_NEUTRAL = color.rgb32(56, 189, 248)

RESULT_TITLE_SCALE = 2.3
RESULT_STATS_SCALE = 1.1
RESULT_STATS_SCALE_DETAILED = 0.88
