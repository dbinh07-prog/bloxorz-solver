"""Tên hàm và tham số theo repo tham chiếu; thành viên 2 tự viết phần GUI."""

from pathlib import Path
from ursina import Audio

from ui.theme import (
    UI_CLICK_SOUND,
    UI_HOVER_SOUND,
    UI_CLICK_VOLUME,
    UI_HOVER_VOLUME,
)

_click_audio = None
_hover_audio = None


def _is_audio_valid(audio_obj):
    """Kiểm tra đối tượng Audio còn hợp lệ và có clip âm thanh sẵn sàng."""
    if audio_obj is None:
        return False
    try:
        return hasattr(audio_obj, "clip") and audio_obj.clip is not None
    except Exception:
        return False


def get_click_audio():
    global _click_audio
    if not _is_audio_valid(_click_audio):
        if UI_CLICK_SOUND and Path(UI_CLICK_SOUND).exists():
            try:
                _click_audio = Audio(
                    UI_CLICK_SOUND,
                    autoplay=False,
                    loop=False,
                    volume=UI_CLICK_VOLUME,
                    add_to_scene_entities=False,
                )
                if hasattr(_click_audio, "clip") and _click_audio.clip:
                    _click_audio.clip.setVolume(UI_CLICK_VOLUME)
            except Exception:
                _click_audio = None
    return _click_audio


def get_hover_audio():
    global _hover_audio
    if not _is_audio_valid(_hover_audio):
        if UI_HOVER_SOUND and Path(UI_HOVER_SOUND).exists():
            try:
                _hover_audio = Audio(
                    UI_HOVER_SOUND,
                    autoplay=False,
                    loop=False,
                    volume=UI_HOVER_VOLUME,
                    add_to_scene_entities=False,
                )
                if hasattr(_hover_audio, "clip") and _hover_audio.clip:
                    _hover_audio.clip.setVolume(UI_HOVER_VOLUME)
            except Exception:
                _hover_audio = None
    return _hover_audio


def play_click():
    try:
        audio = get_click_audio()
        if audio and _is_audio_valid(audio):
            if hasattr(audio, "time"):
                audio.time = 0
            if hasattr(audio, "clip") and audio.clip:
                audio.clip.setVolume(UI_CLICK_VOLUME)
                audio.clip.stop()
                audio.clip.play()
            else:
                audio.stop(destroy=False)
                audio.play()
    except Exception:
        pass


def play_hover():
    try:
        audio = get_hover_audio()
        if audio and _is_audio_valid(audio):
            if hasattr(audio, "time"):
                audio.time = 0
            if hasattr(audio, "clip") and audio.clip:
                audio.clip.setVolume(UI_HOVER_VOLUME)
                audio.clip.stop()
                audio.clip.play()
            else:
                audio.stop(destroy=False)
                audio.play()
    except Exception:
        pass
