"""Điều phối chuyển cảnh giữa các màn hình trong ứng dụng. Owner: thành viên 2."""

from ursina import destroy

from game.audio_manager import AudioManager
from game.game import Game
from scenes.level_select_scene import LevelSelectScene
from scenes.menu_scene import MenuScene
from scenes.tutorial_scene import TutorialScene


class AppController:

    def __init__(self):
        # AudioManager dùng chung xuyên suốt vòng đời ứng dụng
        self.audio_manager = AudioManager()
        self.current_scene = None

        # Mở màn hình chính đầu tiên
        self.show_main_menu()

    def input(self, key):
        """Chuyển tiếp sự kiện bàn phím xuống scene hiện hành nếu có."""
        if self.current_scene and hasattr(self.current_scene, "input"):
            self.current_scene.input(key)

    def clear_screen(self):
        """Hủy sạch scene cũ và giải phóng tài nguyên trước khi chuyển cảnh."""
        if self.current_scene is not None:
            if hasattr(self.current_scene, "on_destroy"):
                self.current_scene.on_destroy()

            destroy(self.current_scene)
            self.current_scene = None

    def show_main_menu(self):
        """Hiển thị màn hình Menu chính (MenuScene)."""
        self.clear_screen()
        if self.audio_manager:
            self.audio_manager.play_menu_music()

        self.current_scene = MenuScene(
            on_play=lambda: self.show_level_select("play"),
            on_solve=lambda: self.show_level_select("solve"),
            on_tutorial=self.show_tutorial,
        )

    def show_tutorial(self):
        """Hiển thị màn hình hướng dẫn chơi (TutorialScene)."""
        self.clear_screen()
        if self.audio_manager:
            self.audio_manager.play_menu_music()

        self.current_scene = TutorialScene(
            on_back=self.show_main_menu,
        )

    def show_level_select(self, mode):
        """Hiển thị màn hình chọn level chơi tay hoặc chọn level giải thuật toán (LevelSelectScene)."""
        self.clear_screen()
        if self.audio_manager:
            self.audio_manager.play_menu_music()

        self.current_scene = LevelSelectScene(
            mode=mode,
            on_level_selected=self.handle_level_selected,
            on_back=self.show_main_menu,
        )

    def handle_level_selected(self, level_path, mode, algorithm=None):
        """Nhận sự kiện chọn level từ LevelSelectScene và khởi tạo màn chơi."""
        self.start_game(level_path, mode, algorithm)

    def start_game(self, level_path, mode, algorithm):
        """Khởi động màn chơi 3D (Game)."""
        self.clear_screen()
        if self.audio_manager:
            self.audio_manager.play_gameplay_music()

        self.current_scene = Game(
            level_path=level_path,
            mode=mode,
            algorithm=algorithm,
            on_back=lambda: self.show_level_select(mode),
            audio_manager=self.audio_manager,
        )
