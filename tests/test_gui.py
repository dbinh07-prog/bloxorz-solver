import unittest
from unittest.mock import MagicMock, patch

from actions import ALL_ACTIONS
from block import Block, Orientation
from board import TransitionResult
from game.block_renderer import BlockRenderer
from game.game import Game, format_time, _edge_tip_direction
from game.renderer import Renderer
from scenes.level_select_scene import get_level_number


class BaseGuiTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_audio = MagicMock()

    def create_mock_game(self, level_path="maps/example_basic.json", mode="play", algorithm="BFS"):
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

            game.renderer = mock_renderer_cls.return_value
            game.block_renderer = mock_block_renderer_cls.return_value
            return game


class TestInputMapping(BaseGuiTestCase):

    def test_arrows_and_wasd_mapping(self):
        game = self.create_mock_game()
        game.try_move = MagicMock()

        key_expected_actions = [
            ("up arrow", "UP"),
            ("arrow_up", "UP"),
            ("down arrow", "DOWN"),
            ("arrow_down", "DOWN"),
            ("left arrow", "LEFT"),
            ("arrow_left", "LEFT"),
            ("right arrow", "RIGHT"),
            ("arrow_right", "RIGHT"),
            ("w", "UP"),
            ("s", "DOWN"),
            ("a", "LEFT"),
            ("d", "RIGHT"),
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
        game = self.create_mock_game()
        game.try_move = MagicMock()

        game.block.orientation = Orientation.SPLIT
        for key in ("space", "tab"):
            game.try_move.reset_mock()
            game.input(key)
            game.try_move.assert_called_once_with("SWITCH")

        game.block.orientation = Orientation.STANDING
        for key in ("space", "tab"):
            game.try_move.reset_mock()
            game.input(key)
            game.try_move.assert_not_called()

    def test_invalid_keys_ignored(self):
        game = self.create_mock_game()
        game.try_move = MagicMock()

        for invalid_key in ("x", "enter", "p", "1", "shift", "c", "v"):
            game.try_move.reset_mock()
            game.input(invalid_key)
            game.try_move.assert_not_called()

    def test_input_locked_conditions(self):
        game = self.create_mock_game()
        game.try_move = MagicMock()

        game.is_animating = True
        game.is_game_over = False
        game.mode = "play"
        game.input("w")
        game.try_move.assert_not_called()

        game.is_animating = False
        game.is_game_over = True
        game.mode = "play"
        game.input("w")
        game.try_move.assert_not_called()

        game.is_animating = False
        game.is_game_over = False
        game.mode = "solve"
        game.input("w")
        game.try_move.assert_not_called()


class TestSwitchDelegationContract(BaseGuiTestCase):

    def test_switch_delegates_to_board_transition(self):
        game = self.create_mock_game()

        original_block = Block.split((1, 1), (3, 3), active_index=0)
        game.block = original_block
        self.assertEqual(game.block.active_index, 0)

        switched_block = Block.split((1, 1), (3, 3), active_index=1)
        mock_transition = TransitionResult(
            block=switched_block,
            bridge_states=game.bridge_states,
            activated_switches=(),
            valid=True,
        )
        game.board.transition = MagicMock(return_value=mock_transition)

        game.try_move("SWITCH")

        game.board.transition.assert_called_once_with(original_block, game.bridge_states, "SWITCH")

        game.block_renderer.animate_move.assert_called_once()
        _, kwargs = game.block_renderer.animate_move.call_args
        on_complete = kwargs.get("on_complete")
        self.assertIsNotNone(on_complete)

        on_complete()

        self.assertEqual(game.block.active_index, 1)
        self.assertEqual(game.block, switched_block)


class TestSolverPathReplay(BaseGuiTestCase):

    def test_solver_path_sequential_replay(self):
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

        for i, expected_action in enumerate(test_path):
            self.assertEqual(game.solution_step_index, i)
            game.try_move.reset_mock()
            game.play_next_solution_move()
            game.try_move.assert_called_once_with(expected_action)
            self.assertEqual(game.solution_step_index, i + 1)

        game.try_move.reset_mock()
        game.block = Block(*game.board.goal)
        with patch.object(game, "show_win") as mock_show_win:
            game.play_next_solution_move()
            self.assertFalse(game.is_replaying)
            mock_show_win.assert_called_once()
            game.try_move.assert_not_called()

    def test_solver_no_solution_calls_show_no_solution(self):
        game = self.create_mock_game(mode="solve")
        result = MagicMock(found=False)
        with patch("game.game.SolverJob") as job, patch.object(game, "show_no_solution") as show:
            job.return_value.poll.return_value = (result, None)
            game.start_solver()
            game._poll_solver()
            show.assert_called_once()
            self.assertFalse(game.is_replaying)

    def test_solver_exception_calls_show_solver_error(self):
        game = self.create_mock_game(mode="solve")
        with patch("game.game.SolverJob") as job, patch.object(game, "show_solver_error") as show:
            job.return_value.poll.return_value = (None, "Heuristic Error")
            game.start_solver()
            game._poll_solver()
            self.assertIn("Heuristic Error", show.call_args.args[0])
            self.assertFalse(game.is_replaying)

    def test_solver_start_failure_is_reported(self):
        game = self.create_mock_game(mode="solve")
        with patch("game.game.SolverJob", side_effect=OSError("Cannot start")), patch.object(game, "show_solver_error") as show:
            game.start_solver()
            self.assertIn("Cannot start", show.call_args.args[0])

    def test_pending_solver_returns_control_and_restart_cancels_it(self):
        game = self.create_mock_game(mode="play")
        with patch("game.game.SolverJob") as job:
            job.return_value.poll.return_value = None
            game.start_solver()
            game._poll_solver()
            self.assertIsNone(game.search_result)
            game.restart()
            job.return_value.cancel.assert_called_once()
            self.assertIsNone(game._solver_job)

    def test_replay_cannot_win_before_reaching_goal(self):
        game = self.create_mock_game()
        game.is_replaying = True
        game.solution_path = []
        with patch.object(game, "show_solver_error") as show, patch.object(game, "show_win") as win:
            game.play_next_solution_move()
            show.assert_called_once()
            win.assert_not_called()


class TestHelperAndCoordinates(unittest.TestCase):

    def test_get_level_number(self):
        self.assertEqual(get_level_number("maps/level_01.json"), 1)
        self.assertEqual(get_level_number("maps/level_12.json"), 12)
        self.assertEqual(get_level_number("maps/level_99.json"), 99)
        self.assertEqual(get_level_number("maps/example_basic.json"), 999999)
        self.assertEqual(get_level_number("custom_test.json"), 999999)

    def test_coordinate_system_consistency(self):
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

                expected_x = float(c)
                expected_y = 0.0
                expected_z = float(-r)

                self.assertEqual(p_renderer.x, expected_x)
                self.assertEqual(p_renderer.y, expected_y)
                self.assertEqual(p_renderer.z, expected_z)

                self.assertEqual(p_block.x, expected_x)
                self.assertEqual(p_block.y, expected_y)
                self.assertEqual(p_block.z, expected_z)

                self.assertEqual(p_renderer, p_block)


class TestGameLifecycle(BaseGuiTestCase):

    def test_game_restart_resets_all_state(self):
        game = self.create_mock_game()

        game.steps = 18
        game.elapsed_time = 54.2
        game.is_game_over = True
        game.time_text.text = "TIME: 00:54"
        game.steps_text.text = "STEPS: 18"
        game.result_panel.enabled = True

        game.restart()

        self.assertEqual(game.steps, 0)
        self.assertEqual(game.elapsed_time, 0.0)
        self.assertFalse(game.is_game_over)
        self.assertFalse(game.is_animating)
        self.assertEqual(game.time_text.text, "TIME: 00:00")
        self.assertEqual(game.steps_text.text, "STEPS: 0")
        self.assertFalse(game.result_panel.enabled)

        game.block_renderer.stop_animations.assert_called()
        game.block_renderer.update_transform.assert_called()
        game.audio_manager.stop_result_sounds.assert_called()

    def test_game_on_destroy_cleans_entities_and_audio(self):
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
        game = self.create_mock_game()
        game.elapsed_time = 18.0
        game.steps = 7

        game.show_lose()

        self.assertTrue(game.is_game_over)
        self.assertIn("Time: 00:18", game.result_stats.text)
        self.assertIn("Steps reached: 7", game.result_stats.text)

    def test_timer_resets_on_restart(self):
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


class TestIntegratedBoardRendering(unittest.TestCase):
    def test_void_cells_do_not_become_floor_tiles(self):
        from board import Board
        board = Board("maps/level_1.json")
        renderer = object.__new__(Renderer)
        renderer.board, renderer.parent, renderer.map_root = board, MagicMock(), None
        with patch("game.renderer.Entity"), patch.object(renderer, "_create_goal_tile"), patch.object(renderer, "_create_floor_tile") as floor:
            renderer.create_map()
        expected = {(r, c) for r in range(board.rows) for c in range(board.cols) if board.is_floor(r, c) and not board.is_goal(r, c)}
        drawn = {tuple(call.args[:2]) for call in floor.call_args_list}
        self.assertEqual(drawn, expected)




class TestStartFallAnimations(BaseGuiTestCase):

    def test_edge_tip_direction_all_directions(self):
        self.assertEqual(_edge_tip_direction((2, 3), (1, 3)), "UP")
        self.assertEqual(_edge_tip_direction((2, 3), (3, 3)), "DOWN")
        self.assertEqual(_edge_tip_direction((2, 3), (2, 2)), "LEFT")
        self.assertEqual(_edge_tip_direction((2, 3), (2, 4)), "RIGHT")
        self.assertEqual(_edge_tip_direction((0, 0), (0, 0)), "DOWN")

    def test_start_fall_edge_tip_animates_move_first_and_uses_correct_tip_dir(self):
        game = self.create_mock_game()

        inv_block = MagicMock()
        inv_block.orientation = Orientation.HORIZONTAL
        inv_block.get_cells.return_value = [(2, 3), (2, 4)]
        inv_block.pos1 = (2, 3)
        inv_block.pos2 = (2, 4)

        game.board.is_floor = MagicMock(side_effect=lambda r, c, states=None: (r, c) == (2, 3))
        game.board.is_fragile = MagicMock(return_value=False)

        transition = MagicMock()
        transition.block = inv_block
        transition.bridge_states = game.bridge_states
        transition.activated_switches = ()
        transition.valid = False

        game.start_fall(transition, "RIGHT")

        game.block_renderer.animate_move.assert_called_once()
        args, kwargs = game.block_renderer.animate_move.call_args
        self.assertEqual(args[0], game.block)
        self.assertEqual(args[1], inv_block)
        self.assertEqual(args[2], "RIGHT")

        game.block_renderer.animate_edge_tip_and_fall.assert_not_called()

        on_complete = kwargs.get("on_complete")
        self.assertIsNotNone(on_complete)
        on_complete()

        self.assertEqual(game.block, inv_block)
        game.block_renderer.animate_edge_tip_and_fall.assert_called_once_with(
            (2, 3),
            "RIGHT",
            on_complete=game.show_lose,
        )

    def test_start_fall_edge_tip_calculates_tip_dir_independent_of_move_direction(self):
        game = self.create_mock_game()

        inv_block = MagicMock()
        inv_block.orientation = Orientation.VERTICAL
        inv_block.get_cells.return_value = [(2, 3), (3, 3)]

        game.board.is_floor = MagicMock(side_effect=lambda r, c, states=None: (r, c) == (3, 3))
        game.board.is_fragile = MagicMock(return_value=False)

        transition = MagicMock()
        transition.block = inv_block
        transition.bridge_states = game.bridge_states
        transition.activated_switches = ()
        transition.valid = False

        game.start_fall(transition, "DOWN")

        _, kwargs = game.block_renderer.animate_move.call_args
        on_complete = kwargs.get("on_complete")
        on_complete()

        game.block_renderer.animate_edge_tip_and_fall.assert_called_once_with(
            (3, 3),
            "UP",
            on_complete=game.show_lose,
        )

    def test_start_fall_edge_tip_canceled_on_session_restart(self):
        game = self.create_mock_game()

        inv_block = MagicMock()
        inv_block.orientation = Orientation.HORIZONTAL
        inv_block.get_cells.return_value = [(2, 3), (2, 4)]
        game.board.is_floor = MagicMock(side_effect=lambda r, c, states=None: (r, c) == (2, 3))
        game.board.is_fragile = MagicMock(return_value=False)

        transition = MagicMock()
        transition.block = inv_block
        transition.bridge_states = game.bridge_states
        transition.activated_switches = ()
        transition.valid = False

        game.start_fall(transition, "RIGHT")
        _, kwargs = game.block_renderer.animate_move.call_args
        on_complete = kwargs.get("on_complete")

        game.restart()

        on_complete()
        game.block_renderer.animate_edge_tip_and_fall.assert_not_called()

    def test_start_fall_switch_closes_bridge_under_block(self):
        game = self.create_mock_game()

        inv_block = MagicMock()
        inv_block.orientation = Orientation.STANDING
        inv_block.get_cells.return_value = [(2, 3)]
        inv_block.pos1 = (2, 3)

        new_bridges = (("b1", False),)
        game.board.is_floor = MagicMock(return_value=False)
        game.board.is_fragile = MagicMock(return_value=False)

        transition = MagicMock()
        transition.block = inv_block
        transition.bridge_states = new_bridges
        transition.activated_switches = ("s1",)
        transition.valid = False

        game.start_fall(transition, "UP")

        game.block_renderer.animate_move.assert_called_once()
        args, kwargs = game.block_renderer.animate_move.call_args
        self.assertEqual(args[2], "UP")
        game.renderer.refresh_bridge_states.assert_not_called()
        game.block_renderer.animate_fall.assert_not_called()

        on_complete = kwargs.get("on_complete")
        on_complete()

        self.assertEqual(game.block, inv_block)
        self.assertEqual(game.bridge_states, new_bridges)
        game.renderer.refresh_bridge_states.assert_called_once_with(new_bridges)
        game.block_renderer.animate_fall.assert_called_once_with(on_complete=game.show_lose)

    def test_start_fall_switch_closes_bridge_edge_tip(self):
        game = self.create_mock_game()

        inv_block = MagicMock()
        inv_block.orientation = Orientation.HORIZONTAL
        inv_block.get_cells.return_value = [(2, 3), (2, 4)]

        new_bridges = (("b1", False),)
        game.board.is_floor = MagicMock(side_effect=lambda r, c, states=None: (r, c) == (2, 3))
        game.board.is_fragile = MagicMock(return_value=False)

        transition = MagicMock()
        transition.block = inv_block
        transition.bridge_states = new_bridges
        transition.activated_switches = ("s1",)
        transition.valid = False

        game.start_fall(transition, "RIGHT")
        _, kwargs = game.block_renderer.animate_move.call_args
        on_complete = kwargs.get("on_complete")
        on_complete()

        game.renderer.refresh_bridge_states.assert_called_once_with(new_bridges)
        game.block_renderer.animate_edge_tip_and_fall.assert_called_once_with(
            (2, 3),
            "RIGHT",
            on_complete=game.show_lose,
        )

    def test_start_fall_switch_closes_bridge_under_split_cube(self):
        game = self.create_mock_game()

        inv_block = MagicMock()
        inv_block.orientation = Orientation.SPLIT
        inv_block.pos1 = (2, 3)
        inv_block.pos2 = (5, 5)

        new_bridges = (("b1", False),)
        # Ô (2, 3) bị sập cầu, ô (5, 5) vẫn còn sàn
        game.board.is_floor = MagicMock(side_effect=lambda r, c, states=None: (r, c) == (5, 5))
        game.board.is_fragile = MagicMock(return_value=False)

        transition = MagicMock()
        transition.block = inv_block
        transition.bridge_states = new_bridges
        transition.activated_switches = ("s1",)
        transition.valid = False

        game.start_fall(transition, "UP")
        _, kwargs = game.block_renderer.animate_move.call_args
        on_complete = kwargs.get("on_complete")
        on_complete()

        game.renderer.refresh_bridge_states.assert_called_once_with(new_bridges)
        game.block_renderer.animate_split_fall.assert_called_once_with(
            [(5, 5)],
            on_complete=game.show_lose,
        )

    def test_start_fall_switch_canceled_on_session_restart(self):
        game = self.create_mock_game()

        inv_block = MagicMock()
        inv_block.orientation = Orientation.STANDING
        inv_block.get_cells.return_value = [(2, 3)]
        inv_block.pos1 = (2, 3)
        game.board.is_floor = MagicMock(return_value=False)
        game.board.is_fragile = MagicMock(return_value=False)

        transition = MagicMock()
        transition.block = inv_block
        transition.bridge_states = (("b1", False),)
        transition.activated_switches = ("s1",)
        transition.valid = False

        game.start_fall(transition, "UP")
        _, kwargs = game.block_renderer.animate_move.call_args
        on_complete = kwargs.get("on_complete")

        game.restart()
        game.renderer.refresh_bridge_states.reset_mock()
        game.block_renderer.animate_fall.reset_mock()

        on_complete()
        game.renderer.refresh_bridge_states.assert_not_called()
        game.block_renderer.animate_fall.assert_not_called()


if __name__ == "__main__":
    unittest.main()
