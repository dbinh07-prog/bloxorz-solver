from pathlib import Path

from ursina import (
    Entity,
    Text,
    Vec3,
    camera,
    color,
    destroy,
    invoke,
    time as utime,
)
from ursina.models.procedural.quad import Quad

from algorithms.worker import SolverJob
from actions import ALL_ACTIONS
from block import Block, Orientation
from board import Board, TransitionResult
from game.audio_manager import AudioManager
from game.block_renderer import BlockRenderer
from game.camera_controller import setup_camera
from game.renderer import Renderer
from ui.menu_button import MenuTextButton
from ui.rotating_cube import RotatingCube
from ui.theme import (
    FONT_BOLD,
    FONT_REGULAR,
    FONT_TITLE,
    GRAY,
    PRIMARY,
    RESULT_PANEL_SCALE,
    RESULT_PANEL_TINT_LOSE,
    RESULT_PANEL_TINT_NEUTRAL,
    RESULT_PANEL_TINT_WIN,
    RESULT_STATS_SCALE,
    RESULT_STATS_SCALE_DETAILED,
    RESULT_TITLE_COLOR_LOSE,
    RESULT_TITLE_COLOR_NEUTRAL,
    RESULT_TITLE_COLOR_WIN,
    WHITE,
)


def format_time(seconds):
    seconds = max(0.0, float(seconds))
    total_secs = int(seconds)
    hours = total_secs // 3600
    mins = (total_secs % 3600) // 60
    secs = total_secs % 60
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class Game(Entity):

    def __init__(self, level_path, mode="play", algorithm=None, on_back=None, audio_manager=None):
        super().__init__()

        self.level_path = str(level_path)
        self.mode = mode
        self.algorithm = algorithm
        self.on_back = on_back
        self.audio_manager = audio_manager if audio_manager else AudioManager()
        if hasattr(self.audio_manager, "play_gameplay_music"):
            self.audio_manager.play_gameplay_music()

        self._load_game_data()

        self.scene_3d_root = Entity()
        self.ui_root = Entity(parent=camera.ui)

        setup_camera(self.board)

        game_bg_candidates = [
            "assets/sprites/Background.png",
            "assets/sprites/background.png",
            "assets/sprites/Background.jpg",
            "assets/sprites/background.jpg",
        ]
        game_bg = None
        for cand in game_bg_candidates:
            if Path(cand).exists():
                game_bg = cand
                break

        if game_bg:
            import math
            dist = 150.0
            fov = getattr(camera, "fov", 45.0)
            h = 2.0 * dist * math.tan(math.radians(fov / 2.0))
            aspect = getattr(camera, "aspect_ratio", 16 / 9)
            w = h * aspect
            self.background = Entity(
                parent=camera,
                model="quad",
                texture=game_bg,
                scale=(w, h),
                position=(0, 0, dist),
                unlit=True,
                double_sided=True,
            )
            try:
                self.background.setBin("background", 0)
                self.background.setDepthWrite(False)
            except Exception:
                pass
        else:
            self.background = None

        self.renderer = Renderer(self.board, self.scene_3d_root)
        self.block_renderer = BlockRenderer(self.block, self.scene_3d_root)

        self.steps = 0
        self.elapsed_time = 0.0
        self._last_displayed_sec = -1
        self._play_session = 0
        self.is_animating = False
        self.is_game_over = False
        self.is_replaying = False
        self.solution_path = []
        self.solution_step_index = 0
        self.search_result = None
        self._solver_job = None

        self.create_ui()
        self.create_result_panel()

        if self.mode == "solve":
            self._schedule(self.start_solver, delay=0.35)

    def _load_game_data(self):
        self.board = Board(self.level_path)
        self.block = Block(*self.board.start)
        self.bridge_states = self.board.initial_bridge_states

    def _schedule(self, callback, delay):
        session = self._play_session
        invoke(lambda: callback() if self._play_session == session else None, delay=delay)

    def _cancel_solver(self):
        if self._solver_job is not None:
            self._solver_job.cancel()
            self._solver_job = None

    def start_solver(self):
        self._cancel_solver()
        try:
            self._solver_job = SolverJob(
                self.level_path, self.block, self.bridge_states, self.algorithm,
            )
        except Exception as error:
            self.show_solver_error(f"Lỗi Solver: {error}")

    def _poll_solver(self):
        if self._solver_job is None:
            return
        message = self._solver_job.poll()
        if message is None:
            return
        self._solver_job = None
        self.search_result, error = message
        if error is not None:
            self.show_solver_error(f"Lỗi Solver: {error}")
            return
        if not self.search_result.found:
            self.show_no_solution()
            return
        self.solution_path = list(self.search_result.path)
        self.solution_step_index = 0
        self.is_replaying = True
        self.play_next_solution_move()

    def play_next_solution_move(self):
        if not self.is_replaying or self.is_game_over:
            return

        if self.solution_step_index >= len(self.solution_path):
            self.is_replaying = False
            if not self.is_game_over:
                if self.board.is_win(self.block):
                    self.show_win()
                else:
                    self.show_solver_error("Đường đi kết thúc nhưng khối chưa tới đích.")
            return

        action = self.solution_path[self.solution_step_index]
        self.solution_step_index += 1
        self.try_move(action)

    def update(self):
        self._poll_solver()
        if hasattr(self, "background") and self.background:
            import math
            dist = 150.0
            fov = getattr(camera, "fov", 45.0)
            h = 2.0 * dist * math.tan(math.radians(fov / 2.0))
            aspect = getattr(camera, "aspect_ratio", 16 / 9)
            w = h * aspect
            self.background.scale = (w, h)

        if not self.is_game_over:
            dt = getattr(utime, "dt", 0.0)
            if dt > 0:
                self.elapsed_time += min(dt, 0.1)
                cur_sec = int(self.elapsed_time)
                if cur_sec != self._last_displayed_sec:
                    self._last_displayed_sec = cur_sec
                    if hasattr(self, "time_text") and self.time_text:
                        self.time_text.text = f"TIME: {self.format_time(self.elapsed_time)}"

    def input(self, key):
        if self.is_animating or self.is_game_over:
            if key in ("r", "R"):
                self.restart()
            elif key == "escape":
                self.back_to_level_select()
            return

        if self.mode == "solve":
            if key in ("r", "R"):
                self.restart()
            elif key == "escape":
                self.back_to_level_select()
            return

        if key in ("r", "R"):
            self.restart()
            return
        elif key == "escape":
            self.back_to_level_select()
            return

        k = key.lower() if isinstance(key, str) else key
        key_map = {
            "w": "UP",
            "up arrow": "UP",
            "arrow_up": "UP",
            "s": "DOWN",
            "down arrow": "DOWN",
            "arrow_down": "DOWN",
            "a": "LEFT",
            "left arrow": "LEFT",
            "arrow_left": "LEFT",
            "d": "RIGHT",
            "right arrow": "RIGHT",
            "arrow_right": "RIGHT",
            "space": "SWITCH",
            "tab": "SWITCH",
        }

        if k in key_map:
            action = key_map[k]
            if action == "SWITCH":
                ori = getattr(self.block, "orientation", Orientation.STANDING)
                is_split = ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3
                if not is_split:
                    return

            self.try_move(action)

    def try_move(self, action):
        if action not in ALL_ACTIONS:
            return

        self.is_animating = True

        transition = self.board.transition(self.block, self.bridge_states, action)

        if transition.valid:
            self.audio_manager.play_move_sound()
            self.block_renderer.animate_move(
                self.block,
                transition.block,
                action,
                on_complete=lambda: self.finish_move(transition),
            )
        else:
            self.start_fall(transition, action)

    def finish_move(self, transition):
        self.block = transition.block
        self.bridge_states = transition.bridge_states
        self.renderer.refresh_bridge_states(self.bridge_states)

        self.steps += 1
        if hasattr(self, "steps_text") and self.steps_text:
            self.steps_text.text = f"STEPS: {self.steps}"

        if self.board.is_win(self.block):
            self.is_animating = True
            self.is_game_over = True
            self.is_replaying = False
            current_session = self._play_session

            def _on_win_fall_complete():
                if getattr(self, "_play_session", 0) == current_session:
                    self.show_win()

            if hasattr(self.block_renderer, "animate_goal_fall"):
                self.block_renderer.animate_goal_fall(on_complete=_on_win_fall_complete)
            else:
                self.block_renderer.animate_fall(on_complete=_on_win_fall_complete, rotate=False, distance=2.05)
        else:
            self.is_animating = False
            if self.is_replaying:
                self._schedule(self.play_next_solution_move, delay=0.12)

    def start_fall(self, transition, direction):
        self.audio_manager.play_lose_sound()

        inv_block = getattr(transition, "block", None) or self.block
        new_bridges = getattr(transition, "bridge_states", self.bridge_states)

        ori_old = getattr(self.block, "orientation", Orientation.STANDING)
        is_old_split = ori_old == Orientation.SPLIT or (hasattr(ori_old, "name") and ori_old.name == "SPLIT") or ori_old == 3

        ori_inv = getattr(inv_block, "orientation", Orientation.STANDING)
        is_inv_standing = ori_inv == Orientation.STANDING or (hasattr(ori_inv, "name") and ori_inv.name == "STANDING") or ori_inv == 0

        if is_inv_standing and hasattr(self.board, "is_fragile") and self.board.is_fragile(*inv_block.pos1):
            self.block_renderer.animate_move(
                self.block,
                inv_block,
                direction,
                on_complete=lambda: self.block_renderer.animate_fall(on_complete=self.show_lose),
            )
            return

        if is_old_split:
            active_idx = getattr(self.block, "active_index", 0)
            active_cell = inv_block.pos1 if active_idx == 0 else inv_block.pos2

            is_floor = hasattr(self.board, "is_floor") and self.board.is_floor(active_cell[0], active_cell[1], new_bridges)
            if not is_floor:
                self.block_renderer.animate_tip_and_fall(inv_block, direction, on_complete=self.show_lose)
                return

            supported = []
            for cell in (self.block.pos1, self.block.pos2):
                if hasattr(self.board, "is_floor") and self.board.is_floor(cell[0], cell[1], new_bridges):
                    supported.append(cell)
            self.block_renderer.animate_split_fall(supported, on_complete=self.show_lose)
            return

        cells = inv_block.get_cells() if hasattr(inv_block, "get_cells") else []
        supported_cells = [
            c for c in cells
            if hasattr(self.board, "is_floor") and self.board.is_floor(c[0], c[1], new_bridges)
        ]
        if len(supported_cells) == 1:
            self.block_renderer.animate_edge_tip_and_fall(
                supported_cells[0],
                direction,
                on_complete=self.show_lose,
            )
            return

        self.block_renderer.animate_tip_and_fall(
            inv_block,
            direction,
            on_complete=self.show_lose,
        )

    def create_ui(self):
        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}
        font_bold_kwargs = {"font": FONT_BOLD or FONT_REGULAR} if (FONT_BOLD or FONT_REGULAR) else {}

        self.back_button = MenuTextButton(
            text="BACK",
            font=FONT_REGULAR,
            parent=self.ui_root,
            position=(-0.68, 0.42, -0.05),
            text_scale=1.05,
            label_origin=(0, 0),
            hitbox_origin=(0, 0),
            hitbox_width=0.20,
            on_click=self.back_to_level_select,
        )

        level_stem = Path(self.level_path).stem.replace("example_", "").replace("level_", "").replace("_", " ").upper()
        mode_label = f"SOLVER: {self.algorithm}" if self.mode == "solve" else "MANUAL PLAY"
        header_text = f"LEVEL: {level_stem}  |  {mode_label}"

        self.title_text = Text(
            parent=self.ui_root,
            text=header_text,
            origin=(0, 0),
            position=(0, 0.45, -0.05),
            scale=0.88,
            color=GRAY,
            **font_kwargs,
        )

        self.steps_text = Text(
            parent=self.ui_root,
            text="STEPS: 0",
            origin=(0, 0),
            position=(-0.16, 0.40, -0.05),
            scale=1.15,
            color=PRIMARY,
            **font_bold_kwargs,
        )

        self.hud_separator = Text(
            parent=self.ui_root,
            text="|",
            origin=(0, 0),
            position=(0, 0.40, -0.05),
            scale=1.0,
            color=GRAY,
            **font_kwargs,
        )

        self.time_text = Text(
            parent=self.ui_root,
            text="TIME: 00:00",
            origin=(0, 0),
            position=(0.16, 0.40, -0.05),
            scale=1.15,
            color=PRIMARY,
            **font_bold_kwargs,
        )

        self.restart_button = MenuTextButton(
            text="RESTART",
            font=FONT_REGULAR,
            parent=self.ui_root,
            position=(0.68, 0.42, -0.05),
            text_scale=1.05,
            label_origin=(0, 0),
            hitbox_origin=(0, 0),
            hitbox_width=0.22,
            on_click=self.restart,
        )

        hint_msg = (
            "REPLAYING AI SOLUTION...  |  R: Restart  |  ESC: Back"
            if self.mode == "solve"
            else "WASD / Arrows: Roll  |  SPACE / TAB: Switch Cube  |  R: Restart  |  ESC: Back"
        )
        self.hint_text = Text(
            parent=self.ui_root,
            text=hint_msg,
            origin=(0, 0),
            position=(0, -0.45, -0.05),
            scale=0.72,
            color=GRAY,
            **font_kwargs,
        )

    def create_result_panel(self):
        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}
        font_bold_kwargs = {"font": FONT_BOLD or FONT_REGULAR} if (FONT_BOLD or FONT_REGULAR) else {}

        self.result_panel = Entity(parent=self.ui_root, enabled=False, z=-0.10)

        self.result_overlay = Entity(
            parent=self.result_panel,
            model="quad",
            scale=(camera.aspect_ratio * 2.2, 2.2),
            color=color.rgba32(10, 14, 24, 210),
            position=(0, 0, 0.02),
        )

        self.result_box = Entity(
            parent=self.result_panel,
            model=Quad(radius=0.04, aspect=RESULT_PANEL_SCALE[0] / RESULT_PANEL_SCALE[1]),
            scale=RESULT_PANEL_SCALE,
            color=RESULT_PANEL_TINT_WIN,
            position=(0, 0, 0.0),
        )

        self.result_cube = RotatingCube(
            parent=self.result_panel,
            position=(0, 0.31, -0.04),
            scale=(0.08, 0.14, 0.08),
        )

        self.result_title = Text(
            parent=self.result_panel,
            text="STAGE CLEARED!",
            origin=(0, 0),
            position=(0, 0.185, -0.02),
            scale=1.9,
            color=RESULT_TITLE_COLOR_WIN,
            **font_bold_kwargs,
        )

        self.result_subtitle = Text(
            parent=self.result_panel,
            text="",
            origin=(0, 0),
            position=(0, 0.105, -0.02),
            scale=0.85,
            color=WHITE,
            **font_kwargs,
        )

        self.result_stats = Text(
            parent=self.result_panel,
            text="",
            origin=(0, 0),
            position=(0, -0.015, -0.02),
            scale=RESULT_STATS_SCALE,
            color=GRAY,
            line_height=1.25,
            **font_kwargs,
        )

        self.result_restart_btn = MenuTextButton(
            text="RESTART",
            font=FONT_REGULAR,
            parent=self.result_panel,
            position=(-0.18, -0.25, -0.02),
            text_scale=1.1,
            label_origin=(0, 0),
            hitbox_origin=(0, 0),
            hitbox_width=0.26,
            on_click=self.restart,
        )

        self.result_back_btn = MenuTextButton(
            text="LEVELS",
            font=FONT_REGULAR,
            parent=self.result_panel,
            position=(0.18, -0.25, -0.02),
            text_scale=1.1,
            label_origin=(0, 0),
            hitbox_origin=(0, 0),
            hitbox_width=0.26,
            on_click=self.back_to_level_select,
        )

    def _set_result_texts(self, title, subtitle, stats, title_color, stats_scale):
        self.result_title.text = title
        self.result_title.color = title_color
        self.result_subtitle.text = subtitle
        self.result_stats.text = stats
        self.result_stats.scale = stats_scale

    format_time = staticmethod(format_time)

    def show_win(self):
        self.is_game_over = True
        self.audio_manager.play_win_sound()
        time_str = self.format_time(self.elapsed_time)

        if self.mode == "solve" and self.search_result:
            r = self.search_result
            steps = getattr(r, "steps", self.steps)
            cost = getattr(r, "solution_cost", float(self.steps))
            time_sec = getattr(r, "search_time", 0.0)

            try:
                mem_mb = getattr(r, "memory_usage_mb", 0.0)
            except Exception:
                mem_mb = 0.0

            expanded = getattr(r, "expanded_nodes", 0)
            generated = getattr(r, "generated_nodes", 0)
            peak = getattr(r, "peak_frontier", 0)

            stats_msg = (
                f"Steps: {steps}   |   Cost: {cost:.2f}   |   Search: {time_sec:.4f}s\n"
                f"Playtime: {time_str}   |   Expanded: {expanded}   |   Generated: {generated}\n"
                f"Memory: {mem_mb:.2f} MiB   |   Peak Frontier: {peak}"
            )
            subtitle_msg = f"Solver [{self.algorithm}] found a solution!"
            detailed = True
        else:
            stats_msg = f"Time: {time_str}   |   Total Steps: {self.steps}"
            subtitle_msg = "Great Job! Block dropped cleanly into the goal."
            detailed = False

        self._show_result(
            title="STAGE CLEARED!",
            subtitle=subtitle_msg,
            stats=stats_msg,
            outcome="win",
            detailed=detailed,
        )

    def show_lose(self):
        self.is_game_over = True
        time_str = self.format_time(self.elapsed_time)
        self._show_result(
            title="STAGE FAILED!",
            subtitle="The block fell into the abyss.",
            stats=f"Time: {time_str}   |   Steps reached: {self.steps}",
            outcome="lose",
            detailed=False,
        )

    def show_no_solution(self):
        self.is_game_over = True
        self._show_result(
            title="NO SOLUTION FOUND",
            subtitle=f"Solver [{self.algorithm}] searched without finding a path.",
            stats="",
            outcome="neutral",
            detailed=False,
        )

    def show_solver_error(self, message):
        self.is_game_over = True
        self._show_result(
            title="SOLVER ERROR",
            subtitle=str(message)[:75],
            stats="",
            outcome="lose",
            detailed=False,
        )

    def _show_result(self, title, subtitle, stats, outcome, detailed=False, show_cube=True):
        if outcome == "win":
            title_color = RESULT_TITLE_COLOR_WIN
            self.result_box.color = RESULT_PANEL_TINT_WIN
        elif outcome == "lose":
            title_color = RESULT_TITLE_COLOR_LOSE
            self.result_box.color = RESULT_PANEL_TINT_LOSE
        else:
            title_color = RESULT_TITLE_COLOR_NEUTRAL
            self.result_box.color = RESULT_PANEL_TINT_NEUTRAL

        stats_scale = RESULT_STATS_SCALE_DETAILED if detailed else RESULT_STATS_SCALE
        self._set_result_texts(title, subtitle, stats, title_color, stats_scale)

        if hasattr(self, "result_cube") and self.result_cube:
            self.result_cube.enabled = bool(show_cube)

        if hasattr(self, "back_button") and self.back_button:
            self.back_button.enabled = False
        if hasattr(self, "restart_button") and self.restart_button:
            self.restart_button.enabled = False

        self.result_panel.enabled = True

    def back_to_level_select(self):
        self.audio_manager.stop_result_sounds()
        if self.on_back:
            self.on_back()

    def restart(self):
        self.audio_manager.stop_result_sounds()

        self._play_session += 1
        self._cancel_solver()
        self.steps = 0
        self.elapsed_time = 0.0
        self._last_displayed_sec = -1
        self.is_animating = False
        self.is_game_over = False
        self.is_replaying = False
        self.solution_step_index = 0
        self.solution_path = []
        self.search_result = None

        self.block = Block(*self.board.start)
        self.bridge_states = self.board.initial_bridge_states

        self.renderer.refresh_bridge_states(self.bridge_states)

        if hasattr(self, "block_renderer") and self.block_renderer:
            if hasattr(self.block_renderer, "stop_animations"):
                self.block_renderer.stop_animations()
            self.block_renderer.current_block = self.block
            self.block_renderer.update_transform()

        if hasattr(self, "steps_text") and self.steps_text:
            self.steps_text.text = "STEPS: 0"

        if hasattr(self, "time_text") and self.time_text:
            self.time_text.text = "TIME: 00:00"

        if hasattr(self, "result_panel") and self.result_panel:
            self.result_panel.enabled = False

        if hasattr(self, "back_button") and self.back_button:
            self.back_button.enabled = True
        if hasattr(self, "restart_button") and self.restart_button:
            self.restart_button.enabled = True

        if self.mode == "solve":
            self._schedule(self.start_solver, delay=0.35)

    def on_destroy(self):
        self._play_session += 1
        self._cancel_solver()
        self.is_replaying = False
        self.audio_manager.stop_result_sounds()

        if hasattr(self, "block_renderer") and self.block_renderer:
            if hasattr(self.block_renderer, "stop_animations"):
                self.block_renderer.stop_animations()

        if hasattr(self, "background") and self.background:
            destroy(self.background)
            self.background = None

        if hasattr(self, "scene_3d_root") and self.scene_3d_root:
            destroy(self.scene_3d_root)
            self.scene_3d_root = None

        if hasattr(self, "ui_root") and self.ui_root:
            destroy(self.ui_root)
            self.ui_root = None

        self.time_text = None
        self.hud_separator = None
        self.steps_text = None
