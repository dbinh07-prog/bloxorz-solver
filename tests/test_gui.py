"""Bộ Unit Test Tự Động Headless cho GUI 3D (Milestone 5 - Task 5.2).

Tuân thủ nghiêm ngặt:
- Kế thừa unittest.TestCase, kiểm thử tự động không mở cửa sổ đồ họa OpenGL (headless).
- Sử dụng unittest.mock để cô lập toàn bộ thực thể Ursina (Entity, Text, RotatingCube, setup_camera...).
- Tuyệt đối không dùng @unittest.skip. 100% test case chạy thực và PASS.
"""

import unittest
from unittest.mock import MagicMock, patch

from actions import ALL_ACTIONS
from block import Block, Orientation
from board import TransitionResult
from game.block_renderer import BlockRenderer
from game.game import Game, _FallbackBlock, _FallbackBoard, format_time
from game.renderer import Renderer
from scenes.level_select_scene import get_level_number


class BaseGuiTestCase(unittest.TestCase):
    """Lớp cơ sở thiết lập môi trường mock headless cho Game."""

    def setUp(self):
        self.mock_audio = MagicMock()

    def create_mock_game(self, level_path="maps/example_basic.json", mode="play", algorithm="BFS"):
        """Tạo đối tượng Game với các thực thể Ursina được mock an toàn."""
        with patch("game.game.RotatingCube"), \
             patch("game.game.Renderer") as mock_renderer_cls, \
             patch("game.game.BlockRenderer") as mock_block_renderer_cls, \
             patch("game.game.setup_camera"), \
             patch("game.game.Entity"), \
             patch("game.game.Text") as mock_text, \
             patch("game.game.MenuTextButton"):

            mock_text.side_effect = lambda *args, **kwargs: MagicMock()

            game = Game(
                level_path=level_path,
                mode=mode,
                algorithm=algorithm,
                audio_manager=self.mock_audio,
            )

            # Cung cấp mock cụ thể cho các thành phần con nếu cần tương tác
            game.renderer = mock_renderer_cls.return_value
            game.block_renderer = mock_block_renderer_cls.return_value
            return game


class TestInputMapping(BaseGuiTestCase):
    """Test 1: Ánh xạ bàn phím (Input Mapping) trong Game.input()."""

    def test_arrows_and_wasd_mapping(self):
        """Kiểm tra phím mũi tên và WASD (cả chữ thường và chữ hoa) sinh ra action UP/DOWN/LEFT/RIGHT."""
        game = self.create_mock_game()
        game.try_move = MagicMock()

        key_expected_actions = [
            # Mũi tên
            ("up arrow", "UP"),
            ("arrow_up", "UP"),
            ("down arrow", "DOWN"),
            ("arrow_down", "DOWN"),
            ("left arrow", "LEFT"),
            ("arrow_left", "LEFT"),
            ("right arrow", "RIGHT"),
            ("arrow_right", "RIGHT"),
            # WASD chữ thường
            ("w", "UP"),
            ("s", "DOWN"),
            ("a", "LEFT"),
            ("d", "RIGHT"),
            # WASD chữ hoa
            ("W", "UP"),
            ("S", "DOWN"),
            ("A", "LEFT"),
            ("D", "RIGHT"),
        ]

        for key, expected_action in key_expected_actions:
            game.try_move.reset_mock()
            game.input(key)
            game.try_move.assert_called_once_with(expected_action)
            self.assertIn(expected_action, ALL_ACTIONS)

    def test_switch_mapping_split_and_standing(self):
        """Kiểm tra phím Space và Tab chỉ kích hoạt SWITCH khi khối ở trạng thái SPLIT."""
        game = self.create_mock_game()
        game.try_move = MagicMock()

        # 1. Khi đang ở trạng thái SPLIT: Space và Tab phải kích hoạt action SWITCH
        game.block.orientation = Orientation.SPLIT
        for key in ("space", "tab"):
            game.try_move.reset_mock()
            game.input(key)
            game.try_move.assert_called_once_with("SWITCH")

        # 2. Khi ở trạng thái STANDING: Space và Tab không được kích hoạt try_move
        game.block.orientation = Orientation.STANDING
        for key in ("space", "tab"):
            game.try_move.reset_mock()
            game.input(key)
            game.try_move.assert_not_called()

    def test_invalid_keys_ignored(self):
        """Kiểm tra các phím không hợp lệ (x, enter, p, 1...) không kích hoạt try_move."""
        game = self.create_mock_game()
        game.try_move = MagicMock()

        for invalid_key in ("x", "enter", "p", "1", "shift", "c", "v"):
            game.try_move.reset_mock()
            game.input(invalid_key)
            game.try_move.assert_not_called()

    def test_input_locked_conditions(self):
        """Kiểm tra phím điều khiển bị khóa khi is_animating, is_game_over hoặc mode == 'solve'."""
        game = self.create_mock_game()
        game.try_move = MagicMock()

        # 1. Đang chạy diễn hoạt (is_animating == True)
        game.is_animating = True
        game.is_game_over = False
        game.mode = "play"
        game.input("w")
        game.try_move.assert_not_called()

        # 2. Đã kết thúc ván (is_game_over == True)
        game.is_animating = False
        game.is_game_over = True
        game.mode = "play"
        game.input("w")
        game.try_move.assert_not_called()

        # 3. Đang ở chế độ solver giải tự động (mode == 'solve')
        game.is_animating = False
        game.is_game_over = False
        game.mode = "solve"
        game.input("w")
        game.try_move.assert_not_called()


class TestSwitchDelegationContract(BaseGuiTestCase):
    """Test 2: Hợp đồng ủy quyền đổi cube (Switch Delegation Contract)."""

    def test_switch_delegates_to_board_transition(self):
        """Kiểm tra try_move('SWITCH') ủy quyền hoàn toàn cho Board.transition và không tự sửa active_index."""
        game = self.create_mock_game()

        # Thiết lập khối ban đầu ở trạng thái SPLIT với active_index = 0
        original_block = _FallbackBlock(1, 1, (3, 3), Orientation.SPLIT, active_index=0)
        game.block = original_block
        self.assertEqual(game.block.active_index, 0)

        # Mock kết quả transition từ Board
        switched_block = _FallbackBlock(1, 1, (3, 3), Orientation.SPLIT, active_index=1)
        mock_transition = TransitionResult(
            block=switched_block,
            bridge_states=game.bridge_states,
            activated_switches=(),
            valid=True,
        )
        game.board.transition = MagicMock(return_value=mock_transition)

        # Gọi try_move("SWITCH")
        game.try_move("SWITCH")

        # 1. Board.transition phải được gọi đúng tham số
        game.board.transition.assert_called_once_with(original_block, game.bridge_states, "SWITCH")

        # 2. BlockRenderer phải được gọi để animate đổi cube
        game.block_renderer.animate_move.assert_called_once()
        _, kwargs = game.block_renderer.animate_move.call_args
        on_complete = kwargs.get("on_complete")
        self.assertIsNotNone(on_complete)

        # 3. Kích hoạt hoàn tất di chuyển
        on_complete()

        # Khối phải được cập nhật từ kết quả transition của Board
        self.assertEqual(game.block.active_index, 1)
        self.assertEqual(game.block, switched_block)


class TestSolverPathReplay(BaseGuiTestCase):
    """Test 3: Phát lại lời giải của AI Solver (Solver Path Replay)."""

    def test_solver_path_sequential_replay(self):
        """Kiểm tra play_next_solution_move() lấy tuần tự từng action trong path và gọi try_move()."""
        game = self.create_mock_game(mode="solve")
        game.try_move = MagicMock()

        test_path = ["UP", "RIGHT", "DOWN", "SWITCH", "LEFT"]
        mock_search_result = MagicMock()
        mock_search_result.found = True
        mock_search_result.path = test_path

        game.search_result = mock_search_result
        game.solution_path = list(test_path)
        game.solution_step_index = 0
        game.is_replaying = True

        # Duyệt tuần tự từng bước
        for i, expected_action in enumerate(test_path):
            self.assertEqual(game.solution_step_index, i)
            game.try_move.reset_mock()
            game.play_next_solution_move()
            game.try_move.assert_called_once_with(expected_action)
            self.assertEqual(game.solution_step_index, i + 1)

        # Khi hết đường đi (solution_step_index == len(solution_path))
        game.try_move.reset_mock()
        with patch.object(game, "show_win") as mock_show_win:
            game.play_next_solution_move()
            self.assertFalse(game.is_replaying)
            mock_show_win.assert_called_once()
            game.try_move.assert_not_called()

    def test_solver_no_solution_calls_show_no_solution(self):
        """Kiểm tra khi solver trả về found=False thì gọi show_no_solution()."""
        game = self.create_mock_game(mode="solve")

        mock_search_result = MagicMock()
        mock_search_result.found = False

        with patch("algorithms.solver.solve", return_value=mock_search_result), \
             patch.object(game, "show_no_solution") as mock_show_no_sol:
            game.start_solver()
            mock_show_no_sol.assert_called_once()
            self.assertFalse(game.is_replaying)

    def test_solver_exception_calls_show_solver_error(self):
        """Kiểm tra khi solver ném Exception thì Game bắt lỗi và hiển thị show_solver_error()."""
        game = self.create_mock_game(mode="solve")

        with patch("algorithms.solver.solve", side_effect=Exception("Heuristic Error")), \
             patch.object(game, "show_solver_error") as mock_show_err:
            game.start_solver()
            mock_show_err.assert_called_once()
            err_msg = mock_show_err.call_args[0][0]
            self.assertIn("Heuristic Error", err_msg)
            self.assertFalse(game.is_replaying)

    def test_solver_not_implemented_calls_show_solver_error(self):
        """Kiểm tra khi solver ném NotImplementedError thì hiển thị thông báo chưa triển khai."""
        game = self.create_mock_game(mode="solve")

        with patch("algorithms.solver.solve", side_effect=NotImplementedError), \
             patch.object(game, "show_solver_error") as mock_show_err:
            game.start_solver()
            mock_show_err.assert_called_once()
            err_msg = mock_show_err.call_args[0][0]
            self.assertIn("chưa được triển khai", err_msg)
            self.assertFalse(game.is_replaying)


class TestHelperAndCoordinates(unittest.TestCase):
    """Test 4: Hàm phụ trợ get_level_number và tính nhất quán của hệ tọa độ 3D."""

    def test_get_level_number(self):
        """Kiểm tra get_level_number trích xuất đúng số level hoặc trả về 999999."""
        self.assertEqual(get_level_number("maps/level_01.json"), 1)
        self.assertEqual(get_level_number("maps/level_12.json"), 12)
        self.assertEqual(get_level_number("maps/level_99.json"), 99)
        self.assertEqual(get_level_number("maps/example_basic.json"), 999999)
        self.assertEqual(get_level_number("custom_test.json"), 999999)

    def test_coordinate_system_consistency(self):
        """Kiểm tra tính nhất quán giữa Renderer.grid_to_world và BlockRenderer.grid_to_world."""
        with patch("game.renderer.Entity"), patch("game.block_renderer.Entity"):
            mock_board = MagicMock()
            mock_board.rows = 5
            mock_board.cols = 5
            mock_board.grid = [["." for _ in range(5)] for _ in range(5)]
            mock_board.bridges = {}
            mock_board.start = (0, 0)
            mock_board.goal = (4, 4)
            mock_board.initial_bridge_states = ()

            mock_block = MagicMock()
            mock_block.orientation = Orientation.STANDING
            mock_block.pos1 = (0, 0)
            mock_block.pos2 = (0, 0)

            renderer = Renderer(mock_board, MagicMock())
            block_renderer = BlockRenderer(mock_block, MagicMock())

            test_coords = [
                (0, 0),
                (2, 5),
                (8, 3),
                (4, 7),
                (10, 15),
            ]

            for r, c in test_coords:
                p_renderer = renderer.grid_to_world(r, c)
                p_block = block_renderer.grid_to_world(r, c)

                # Quy ước: x = col, y = 0.0, z = -row
                expected_x = float(c)
                expected_y = 0.0
                expected_z = float(-r)

                self.assertEqual(p_renderer.x, expected_x)
                self.assertEqual(p_renderer.y, expected_y)
                self.assertEqual(p_renderer.z, expected_z)

                self.assertEqual(p_block.x, expected_x)
                self.assertEqual(p_block.y, expected_y)
                self.assertEqual(p_block.z, expected_z)

                # Hai renderer phải trùng khớp tuyệt đối
                self.assertEqual(p_renderer, p_block)


class TestGameLifecycle(BaseGuiTestCase):
    """Test 5: Vòng đời Game (Restart & Destroy)."""

    def test_game_restart_resets_all_state(self):
        """Kiểm tra Game.restart() reset các chỉ số steps, elapsed_time, vị trí khối và bridge states."""
        game = self.create_mock_game()

        # Thay đổi trạng thái như khi đang chơi dở
        game.steps = 18
        game.elapsed_time = 54.2
        game.is_game_over = True
        game.time_text.text = "TIME: 00:54"
        game.steps_text.text = "STEPS: 18"
        game.result_panel.enabled = True

        game.restart()

        # Kiểm tra reset hoàn toàn
        self.assertEqual(game.steps, 0)
        self.assertEqual(game.elapsed_time, 0.0)
        self.assertFalse(game.is_game_over)
        self.assertFalse(game.is_animating)
        self.assertEqual(game.time_text.text, "TIME: 00:00")
        self.assertEqual(game.steps_text.text, "STEPS: 0")
        self.assertFalse(game.result_panel.enabled)

        # Kiểm tra các lệnh gọi renderer
        game.block_renderer.stop_animations.assert_called()
        game.block_renderer.update_transform.assert_called()
        game.audio_manager.stop_result_sounds.assert_called()

    def test_game_on_destroy_cleans_entities_and_audio(self):
        """Kiểm tra Game.on_destroy() dọn dẹp sạch sẽ các entity và dừng âm thanh kết quả."""
        game = self.create_mock_game()

        game.on_destroy()

        self.assertFalse(game.is_replaying)
        game.audio_manager.stop_result_sounds.assert_called()
        game.block_renderer.stop_animations.assert_called()

        self.assertIsNone(game.background)
        self.assertIsNone(game.scene_3d_root)
        self.assertIsNone(game.ui_root)
        self.assertIsNone(game.time_text)
        self.assertIsNone(game.steps_text)


class TestGameTimerAndGoalFall(BaseGuiTestCase):
    """Test 6: Kiểm tra tính năng tính thời gian chơi (Time HUD) và hoạt ảnh vào ô Goal."""

    def test_format_time_zero(self):
        self.assertEqual(format_time(0), "00:00")
        self.assertEqual(format_time(0.0), "00:00")
        self.assertEqual(format_time(-5), "00:00")

    def test_format_time_seconds_under_minute(self):
        self.assertEqual(format_time(9), "00:09")
        self.assertEqual(format_time(45.8), "00:45")
        self.assertEqual(format_time(59.99), "00:59")

    def test_format_time_minutes(self):
        self.assertEqual(format_time(60), "01:00")
        self.assertEqual(format_time(75), "01:15")
        self.assertEqual(format_time(605.2), "10:05")
        self.assertEqual(format_time(3599), "59:59")

    def test_format_time_hours(self):
        self.assertEqual(format_time(3600), "01:00:00")
        self.assertEqual(format_time(3665), "01:01:05")
        self.assertEqual(format_time(7325), "02:02:05")

    def test_timer_initialization_and_update(self):
        """Kiểm tra khởi tạo elapsed_time và cập nhật qua các frame."""
        game = self.create_mock_game()
        self.assertEqual(game.elapsed_time, 0.0)
        self.assertEqual(game._last_displayed_sec, -1)
        self.assertFalse(game.is_game_over)

        with patch("game.game.utime") as mock_utime:
            mock_utime.dt = 0.5
            game.update()
            self.assertAlmostEqual(game.elapsed_time, 0.1)

            for _ in range(10):
                game.update()
            self.assertGreaterEqual(game.elapsed_time, 1.0)
            self.assertEqual(game._last_displayed_sec, int(game.elapsed_time))
            self.assertIn("TIME: 00:01", game.time_text.text)

    def test_timer_stops_on_win_and_shows_in_result(self):
        """Kiểm tra dừng đếm giờ khi thắng và hiển thị lên Result Panel."""
        game = self.create_mock_game()
        game.elapsed_time = 42.5
        game.steps = 15

        game.show_win()

        self.assertTrue(game.is_game_over)
        self.assertIn("Time: 00:42", game.result_stats.text)
        self.assertIn("Total Steps: 15", game.result_stats.text)

        with patch("game.game.utime") as mock_utime:
            mock_utime.dt = 0.1
            game.update()
            self.assertEqual(game.elapsed_time, 42.5)

    def test_timer_stops_on_lose_and_shows_in_result(self):
        """Kiểm tra dừng đếm giờ khi thua và hiển thị lên Result Panel."""
        game = self.create_mock_game()
        game.elapsed_time = 18.0
        game.steps = 7

        game.show_lose()

        self.assertTrue(game.is_game_over)
        self.assertIn("Time: 00:18", game.result_stats.text)
        self.assertIn("Steps reached: 7", game.result_stats.text)

    def test_timer_resets_on_restart(self):
        """Kiểm tra reset timer về 00:00 khi restart."""
        game = self.create_mock_game()
        game.elapsed_time = 99.0
        game.steps = 30
        game.is_game_over = True

        game.restart()

        self.assertEqual(game.elapsed_time, 0.0)
        self.assertEqual(game._last_displayed_sec, -1)
        self.assertEqual(game.steps, 0)
        self.assertFalse(game.is_game_over)
        self.assertEqual(game.time_text.text, "TIME: 00:00")
        self.assertEqual(game.steps_text.text, "STEPS: 0")

    def test_win_triggers_fall_animation(self):
        """Kiểm tra khi chạm goal kích hoạt hoạt ảnh animate_goal_fall."""
        game = self.create_mock_game()

        winning_block = MagicMock()
        game.board.is_win = MagicMock(return_value=True)

        mock_trans = MagicMock()
        mock_trans.block = winning_block
        mock_trans.bridge_states = ()

        game.finish_move(mock_trans)

        game.block_renderer.animate_goal_fall.assert_called_once()
        _, kwargs = game.block_renderer.animate_goal_fall.call_args
        self.assertTrue(game.is_animating)
        self.assertTrue(game.is_game_over)

        on_complete = kwargs.get("on_complete")
        self.assertIsNotNone(on_complete)
        with patch.object(game, "show_win") as mock_show_win:
            on_complete()
            mock_show_win.assert_called_once()

    def test_restart_cancels_win_fall_callback(self):
        """Kiểm tra ấn restart hủy callback hoàn tất của session cũ."""
        game = self.create_mock_game()

        winning_block = MagicMock()
        game.board.is_win = MagicMock(return_value=True)
        mock_trans = MagicMock()
        mock_trans.block = winning_block
        mock_trans.bridge_states = ()

        game.finish_move(mock_trans)

        _, kwargs = game.block_renderer.animate_goal_fall.call_args
        on_complete = kwargs.get("on_complete")

        game.restart()
        self.assertFalse(game.is_game_over)

        with patch.object(game, "show_win") as mock_show_win:
            on_complete()
            mock_show_win.assert_not_called()

    @patch("game.block_renderer.Entity")
    @patch("game.block_renderer.invoke")
    def test_block_renderer_animate_goal_fall(self, mock_invoke, mock_entity):
        """Kiểm tra hoạt ảnh vào ô goal: đáy khối giữ ở y=0.0, chiều cao hạ về 0 và mờ dần."""
        mock_block = MagicMock()
        mock_block.orientation = Orientation.STANDING
        mock_block.pos1 = (4, 4)
        mock_block.pos2 = (4, 4)

        renderer = BlockRenderer(mock_block, MagicMock())
        renderer.block_entity = MagicMock()
        renderer.block_entity.y = 1.0
        renderer.block_entity.scale_y = 2.0

        mock_cb = MagicMock()
        renderer.animate_goal_fall(on_complete=mock_cb)

        renderer.block_entity.animate_y.assert_called_with(0.0, duration=unittest.mock.ANY, curve=unittest.mock.ANY)
        renderer.block_entity.animate_scale_y.assert_called_with(0.0, duration=unittest.mock.ANY, curve=unittest.mock.ANY)
        renderer.block_entity.animate_color.assert_called_once()

        mock_invoke.assert_called_once()
        cleanup_fn = mock_invoke.call_args[0][0]
        cleanup_fn()

        self.assertFalse(renderer.block_entity.enabled)
        mock_cb.assert_called_once()


if __name__ == "__main__":
    unittest.main()
