from pathlib import Path
from ursina import Audio, destroy

from ui.theme import (
    WIN_SOUND,
    LOSE_SOUND,
    WIN_SOUND_VOLUME,
    LOSE_SOUND_VOLUME,
    MUSIC_DUCK_VOLUME,
)


def _is_audio_valid(audio_obj):
    if audio_obj is None:
        return False
    try:
        return hasattr(audio_obj, "clip") and audio_obj.clip is not None
    except Exception:
        return False


class AudioManager:

    def __init__(self, parent=None):
        self.parent = parent

        self.music_volume = 0.55
        self.sfx_volume = 0.70
        self.ambient_volume_scale = 0.35
        self.is_gameplay_bgm = False
        self.is_music_muted = False
        self.is_ducked = False

        self.bgm = None
        self.current_track = None
        self.win_audio = None
        self.lose_audio = None
        self.move_audios = []
        self._move_idx = 0

        self._init_sounds()

    def play_music(self, track_path, loop=True):
        if not track_path:
            return

        p = Path(track_path)
        if not p.exists():
            return

        resolved_str = str(p.resolve())

        if self.current_track == resolved_str and _is_audio_valid(self.bgm):
            self._apply_music_volume()
            try:
                if not getattr(self.bgm, "playing", False):
                    self.bgm.play()
            except Exception:
                pass
            return

        if self.bgm is not None:
            try:
                self.bgm.stop()
            except Exception:
                pass
            try:
                destroy(self.bgm)
            except Exception:
                pass
            self.bgm = None

        self.current_track = resolved_str
        self.is_ducked = False

        base_vol = self.music_volume * (self.ambient_volume_scale if self.is_gameplay_bgm else 1.0)
        if self.is_music_muted:
            target_vol = 0.0
        elif self.is_ducked:
            target_vol = min(base_vol, MUSIC_DUCK_VOLUME)
        else:
            target_vol = base_vol

        try:
            self.bgm = Audio(
                str(track_path),
                autoplay=True,
                loop=loop,
                volume=target_vol,
                add_to_scene_entities=False,
            )
        except Exception:
            self.bgm = None

    def play_menu_music(self):
        self.is_gameplay_bgm = False
        menu_candidates = [
            "assets/sounds/01. Menu.mp3",
            "assets/sounds/menu.mp3",
            "assets/sounds/music.mp3",
        ]
        for candidate in menu_candidates:
            if Path(candidate).exists():
                self.play_music(candidate, loop=True)
                return

    def play_gameplay_music(self):
        self.is_gameplay_bgm = True
        gameplay_candidates = [
            "assets/sounds/02. Ambient.mp3",
            "assets/sounds/ambient.mp3",
            "assets/sounds/gameplay.mp3",
            "assets/sounds/01. Menu.mp3",
        ]
        for candidate in gameplay_candidates:
            if Path(candidate).exists():
                self.play_music(candidate, loop=True)
                return

    def _init_sounds(self):
        self.play_menu_music()

        win_candidates = [
            "assets/sounds/Win.mp3",
            "assets/sounds/win.mp3",
            "assets/sounds/win.wav",
            WIN_SOUND,
            "assets/sounds/block_land.wav",
        ]
        win_path = None
        for candidate in win_candidates:
            if candidate and Path(candidate).exists():
                win_path = candidate
                break

        if win_path:
            try:
                self.win_audio = Audio(
                    win_path,
                    autoplay=False,
                    loop=False,
                    volume=WIN_SOUND_VOLUME * self.sfx_volume,
                    add_to_scene_entities=False,
                )
            except Exception:
                self.win_audio = None

        lose_candidates = [
            "assets/sounds/Lose.mp3",
            "assets/sounds/lose.mp3",
            "assets/sounds/lose.wav",
            "assets/sounds/lost.wav",
            LOSE_SOUND,
            "assets/sounds/block_land.wav",
        ]
        lose_path = None
        for candidate in lose_candidates:
            if candidate and Path(candidate).exists():
                lose_path = candidate
                break

        if lose_path:
            try:
                self.lose_audio = Audio(
                    lose_path,
                    autoplay=False,
                    loop=False,
                    volume=LOSE_SOUND_VOLUME * self.sfx_volume,
                    add_to_scene_entities=False,
                )
            except Exception:
                self.lose_audio = None

        move_candidates = [
            "assets/sounds/move.wav",
            "assets/sounds/roll.wav",
            "assets/sounds/block_land.wav",
            "assets/sounds/block_land2.wav",
        ]
        for candidate in move_candidates:
            if Path(candidate).exists():
                try:
                    audio_item = Audio(
                        candidate,
                        autoplay=False,
                        loop=False,
                        volume=self.sfx_volume,
                        add_to_scene_entities=False,
                    )
                    if _is_audio_valid(audio_item):
                        self.move_audios.append(audio_item)
                        break
                except Exception:
                    pass

    def play_move_sound(self):
        if self.sfx_volume <= 0.0 or not self.move_audios:
            return

        try:
            audio = self.move_audios[self._move_idx % len(self.move_audios)]
            self._move_idx += 1
            if _is_audio_valid(audio):
                if hasattr(audio, "time"):
                    audio.time = 0
                if hasattr(audio, "clip") and audio.clip:
                    audio.clip.stop()
                    audio.clip.play()
                else:
                    audio.stop(destroy=False)
                    audio.play()
        except Exception:
            pass

    def play_win_sound(self):
        self.stop_result_sounds()
        self.duck_music()

        if self.sfx_volume > 0.0 and _is_audio_valid(self.win_audio):
            try:
                if hasattr(self.win_audio, "time"):
                    self.win_audio.time = 0
                if hasattr(self.win_audio, "clip") and self.win_audio.clip:
                    self.win_audio.clip.stop()
                    self.win_audio.clip.play()
                else:
                    self.win_audio.stop(destroy=False)
                    self.win_audio.play()
            except Exception:
                pass

    def play_lose_sound(self):
        self.stop_result_sounds()
        self.duck_music()

        if self.sfx_volume > 0.0 and _is_audio_valid(self.lose_audio):
            try:
                if hasattr(self.lose_audio, "time"):
                    self.lose_audio.time = 0
                if hasattr(self.lose_audio, "clip") and self.lose_audio.clip:
                    self.lose_audio.clip.stop()
                    self.lose_audio.clip.play()
                else:
                    self.lose_audio.stop(destroy=False)
                    self.lose_audio.play()
            except Exception:
                pass

    def stop_result_sounds(self):
        try:
            if _is_audio_valid(self.win_audio):
                if hasattr(self.win_audio, "clip") and self.win_audio.clip:
                    self.win_audio.clip.stop()
                else:
                    self.win_audio.stop(destroy=False)
        except Exception:
            pass

        try:
            if _is_audio_valid(self.lose_audio):
                if hasattr(self.lose_audio, "clip") and self.lose_audio.clip:
                    self.lose_audio.clip.stop()
                else:
                    self.lose_audio.stop(destroy=False)
        except Exception:
            pass

        self.restore_music()

    def _apply_music_volume(self):
        if not _is_audio_valid(self.bgm):
            return

        base_vol = self.music_volume * (self.ambient_volume_scale if self.is_gameplay_bgm else 1.0)
        if self.is_music_muted:
            target_vol = 0.0
        elif self.is_ducked:
            target_vol = min(base_vol, MUSIC_DUCK_VOLUME)
        else:
            target_vol = base_vol

        try:
            self.bgm.volume = target_vol
        except Exception:
            pass

    def duck_music(self):
        self.is_ducked = True
        self._apply_music_volume()

    def restore_music(self):
        self.is_ducked = False
        self._apply_music_volume()

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, float(volume)))
        self._apply_music_volume()

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, float(volume)))

        try:
            if _is_audio_valid(self.win_audio):
                self.win_audio.volume = WIN_SOUND_VOLUME * self.sfx_volume
            if _is_audio_valid(self.lose_audio):
                self.lose_audio.volume = LOSE_SOUND_VOLUME * self.sfx_volume
            for audio in self.move_audios:
                if _is_audio_valid(audio):
                    audio.volume = self.sfx_volume
        except Exception:
            pass

    def toggle_music(self):
        self.is_music_muted = not self.is_music_muted
        self._apply_music_volume()
        return not self.is_music_muted
