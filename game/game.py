"""Điều phối màn chơi 3D, sự kiện bàn phím, replay lời giải AI và hiển thị kết quả. Owner: thành viên 2."""

import json
from pathlib import Path

from ursina import (
    Entity,
    Text,
    Vec3,
    camera,
    color,
    destroy,
    invoke,
)
from ursina.models.procedural.quad import Quad

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


class _FallbackBlock:
    """Khối thay thế an toàn khi block.py của thành viên 1 chưa hoàn thiện."""

    def __init__(self, r, c, pos2=None, orientation=Orientation.STANDING, active_index=0):
        self.pos1 = (r, c)
        self.pos2 = pos2 if pos2 else (r, c)
        self.orientation = orientation
        self.active_index = active_index

    @property
    def is_split(self):
        ori = self.orientation
        return ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3

    def copy(self):
        return _FallbackBlock(self.pos1[0], self.pos1[1], self.pos2, self.orientation, self.active_index)

    def get_cells(self):
        ori = self.orientation
        is_standing = ori == Orientation.STANDING or (hasattr(ori, "name") and ori.name == "STANDING") or ori == 0
        if is_standing:
            return [self.pos1]
        return [self.pos1, self.pos2]


class _FallbackBoard:
    """Bàn cờ thay thế an toàn đọc trực tiếp JSON khi board.py chưa hoàn thiện."""

    def __init__(self, level_path):
        with open(level_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.grid = data.get("grid", [])
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows > 0 else 0
        self.start = tuple(data.get("start", [0, 0]))
        self.goal = tuple(data.get("goal", [0, 0]))
        self.switches = data.get("switches", [])

        self.bridge_at = {}
        initial_states = []
        for b_id, b_info in data.get("bridges", {}).items():
            initial_states.append((b_id, bool(b_info.get("initial_open", False))))
            for cell in b_info.get("cells", []):
                self.bridge_at[tuple(cell)] = b_id

        initial_states.sort(key=lambda x: x[0])
        self.initial_bridge_states = tuple(initial_states)

    def normalize_bridge_states(self, states=None):
        if states is None:
            return self.initial_bridge_states
        if isinstance(states, dict):
            return tuple(sorted(states.items()))
        return tuple(sorted(states))

    def bridge_state_dict(self, states=None):
        if states is None:
            states = self.initial_bridge_states
        if isinstance(states, dict):
            return states
        return dict(states)

    def is_inside(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def tile_type(self, r, c):
        if self.is_inside(r, c):
            return self.grid[r][c]
        return "#"

    def is_goal(self, r, c):
        return (r, c) == self.goal

    def is_bridge(self, r, c):
        return (r, c) in self.bridge_at

    def is_fragile(self, r, c):
        return self.tile_type(r, c) == "F"

    def get_switch(self, r, c):
        for s in self.switches:
            if tuple(s.get("position", ())) == (r, c):
                return s
        return None

    def is_floor(self, r, c, states=None):
        if not self.is_inside(r, c):
            return False
        if self.is_bridge(r, c):
            s_dict = self.bridge_state_dict(states)
            return s_dict.get(self.bridge_at[(r, c)], False)
        return self.grid[r][c] != "#"

    def is_win(self, block):
        ori = getattr(block, "orientation", Orientation.STANDING)
        is_standing = ori == Orientation.STANDING or (hasattr(ori, "name") and ori.name == "STANDING") or ori == 0
        return is_standing and block.pos1 == self.goal

    def available_actions(self, block):
        actions = ["UP", "DOWN", "LEFT", "RIGHT"]
        ori = getattr(block, "orientation", Orientation.STANDING)
        is_split = ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3
        if is_split:
            actions.append("SWITCH")
        return actions

    def get_action_cost(self, result, action):
        if str(action).upper() == "SWITCH":
            return 0.5
        cost = 1.0
        cells = result.block.get_cells()
        if any(self.is_fragile(r, c) for r, c in cells):
            cost += 1.0
        if getattr(result, "activated_switches", ()):
            cost += 0.25 * len(result.activated_switches)
        return cost

    def transition(self, block, bridge_states, action):
        """Logic transition fallback phục vụ kiểm thử độc lập GUI."""
        b_dict = self.bridge_state_dict(bridge_states)
        act = str(action).upper()
        ori = getattr(block, "orientation", Orientation.STANDING)

        # 1. SWITCH khi đang split
        if act == "SWITCH":
            idx = 1 - getattr(block, "active_index", 0)
            nb = _FallbackBlock(block.pos1[0], block.pos1[1], block.pos2, Orientation.SPLIT, idx)
            return TransitionResult(block=nb, bridge_states=bridge_states, activated_switches=(), valid=True)

        # 2. Di chuyển trong trạng thái SPLIT
        is_split = ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3
        if is_split:
            idx = getattr(block, "active_index", 0)
            dr = -1 if act == "UP" else (1 if act == "DOWN" else 0)
            dc = -1 if act == "LEFT" else (1 if act == "RIGHT" else 0)

            if idx == 0:
                np1 = (block.pos1[0] + dr, block.pos1[1] + dc)
                np2 = block.pos2
                moved_pos = np1
            else:
                np1 = block.pos1
                np2 = (block.pos2[0] + dr, block.pos2[1] + dc)
                moved_pos = np2

            # Kiểm tra merge kề
            if abs(np1[0] - np2[0]) + abs(np1[1] - np2[1]) == 1:
                if np1[0] == np2[0]:
                    left_c = min(np1[1], np2[1])
                    nb = _FallbackBlock(np1[0], left_c, (np1[0], left_c + 1), Orientation.HORIZONTAL)
                else:
                    top_r = min(np1[0], np2[0])
                    nb = _FallbackBlock(top_r, np1[1], (top_r + 1, np1[1]), Orientation.VERTICAL)
            else:
                nb = _FallbackBlock(np1[0], np1[1], np2, Orientation.SPLIT, idx)

            valid = self.is_floor(np1[0], np1[1], bridge_states) and self.is_floor(np2[0], np2[1], bridge_states)
            if not valid:
                return TransitionResult(block=nb, bridge_states=bridge_states, activated_switches=(), valid=False)

            # Xử lý switches cho chế độ SPLIT (chỉ soft switch kích hoạt khi dẫm bởi cube hoặc sau khi merge thành khối nằm)
            new_b_dict = dict(b_dict)
            activated = []
            check_cells = nb.get_cells() if not nb.is_split else [moved_pos]
            for cr, cc in check_cells:
                sw = self.get_switch(cr, cc)
                if sw:
                    sw_type = str(sw.get("type", "")).strip().lower()
                    if not sw_type:
                        tile = self.tile_type(cr, cc)
                        sw_type = "soft" if tile == "S" else ("heavy" if tile == "H" else ("split" if tile == "X" else "soft"))
                    if sw_type == "soft":
                        sw_id = sw.get("id", "")
                        if sw_id and sw_id not in activated:
                            activated.append(sw_id)
                        for b_target in sw.get("bridges", []):
                            action_type = sw.get("action", "toggle")
                            if action_type == "toggle":
                                new_b_dict[b_target] = not new_b_dict.get(b_target, False)
                            elif action_type == "open":
                                new_b_dict[b_target] = True
                            elif action_type == "close":
                                new_b_dict[b_target] = False

            new_b_states = tuple(sorted(new_b_dict.items()))
            return TransitionResult(block=nb, bridge_states=new_b_states, activated_switches=tuple(activated), valid=True)

        # 3. Lăn khối liền chuẩn
        r1, c1 = block.pos1
        r2, c2 = block.pos2
        is_standing = ori == Orientation.STANDING or (hasattr(ori, "name") and ori.name == "STANDING") or ori == 0
        is_horiz = ori == Orientation.HORIZONTAL or (hasattr(ori, "name") and ori.name == "HORIZONTAL") or ori == 1
        is_vert = ori == Orientation.VERTICAL or (hasattr(ori, "name") and ori.name == "VERTICAL") or ori == 2

        if is_standing:
            if act == "UP":
                nb = _FallbackBlock(r1 - 2, c1, (r1 - 1, c1), Orientation.VERTICAL)
            elif act == "DOWN":
                nb = _FallbackBlock(r1 + 1, c1, (r1 + 2, c1), Orientation.VERTICAL)
            elif act == "LEFT":
                nb = _FallbackBlock(r1, c1 - 2, (r1, c1 - 1), Orientation.HORIZONTAL)
            else:
                nb = _FallbackBlock(r1, c1 + 1, (r1, c1 + 2), Orientation.HORIZONTAL)
        elif is_horiz:
            left_c = min(c1, c2)
            if act == "UP":
                nb = _FallbackBlock(r1 - 1, left_c, (r1 - 1, left_c + 1), Orientation.HORIZONTAL)
            elif act == "DOWN":
                nb = _FallbackBlock(r1 + 1, left_c, (r1 + 1, left_c + 1), Orientation.HORIZONTAL)
            elif act == "LEFT":
                nb = _FallbackBlock(r1, left_c - 1, (r1, left_c - 1), Orientation.STANDING)
            else:
                nb = _FallbackBlock(r1, left_c + 2, (r1, left_c + 2), Orientation.STANDING)
        else:  # VERTICAL
            top_r = min(r1, r2)
            if act == "UP":
                nb = _FallbackBlock(top_r - 1, c1, (top_r - 1, c1), Orientation.STANDING)
            elif act == "DOWN":
                nb = _FallbackBlock(top_r + 2, c1, (top_r + 2, c1), Orientation.STANDING)
            elif act == "LEFT":
                nb = _FallbackBlock(top_r, c1 - 1, (top_r + 1, c1 - 1), Orientation.VERTICAL)
            else:
                nb = _FallbackBlock(top_r, c1 + 1, (top_r + 1, c1 + 1), Orientation.VERTICAL)

        # Kiểm tra tính hợp lệ
        cells = nb.get_cells()
        for cr, cc in cells:
            if not self.is_floor(cr, cc, bridge_states):
                return TransitionResult(block=nb, bridge_states=bridge_states, activated_switches=(), valid=False)

        # Đứng trên fragile thì sập
        nb_ori = getattr(nb, "orientation", Orientation.STANDING)
        nb_is_standing = nb_ori == Orientation.STANDING or (hasattr(nb_ori, "name") and nb_ori.name == "STANDING") or nb_ori == 0
        if nb_is_standing and self.is_fragile(*nb.pos1):
            return TransitionResult(block=nb, bridge_states=bridge_states, activated_switches=(), valid=False)

        # Xử lý switches
        new_b_dict = dict(b_dict)
        activated = []
        for cr, cc in cells:
            sw = self.get_switch(cr, cc)
            if not sw:
                continue

            sw_type = str(sw.get("type", "")).strip().lower()
            if not sw_type:
                tile = self.tile_type(cr, cc)
                if tile == "H":
                    sw_type = "heavy"
                elif tile == "X":
                    sw_type = "split"
                elif tile == "S":
                    sw_type = "soft"
                else:
                    sw_type = "soft"

            # 1. Heavy switch: Chỉ kích hoạt khi khối đứng thẳng (standing) trên ô switch
            if sw_type == "heavy":
                if not nb_is_standing:
                    continue

            # 2. Split switch: Chỉ kích hoạt khi khối đứng thẳng (standing) trên ô split switch -> tách thành 2 cube 1x1x1
            if sw_type == "split":
                if not nb_is_standing:
                    continue
                targets = sw.get("targets", [])
                if len(targets) == 2:
                    t1 = tuple(targets[0])
                    t2 = tuple(targets[1])
                    nb = _FallbackBlock(t1[0], t1[1], t2, Orientation.SPLIT, active_index=0)

            # Ghi nhận switch kích hoạt
            sw_id = sw.get("id", "")
            if sw_id and sw_id not in activated:
                activated.append(sw_id)

            # 3. Kích hoạt danh sách cầu liên kết (cho soft, heavy khi đứng, và split khi đứng)
            for b_target in sw.get("bridges", []):
                action_type = sw.get("action", "toggle")
                if action_type == "toggle":
                    new_b_dict[b_target] = not new_b_dict.get(b_target, False)
                elif action_type == "open":
                    new_b_dict[b_target] = True
                elif action_type == "close":
                    new_b_dict[b_target] = False

        new_b_states = tuple(sorted(new_b_dict.items()))
        return TransitionResult(block=nb, bridge_states=new_b_states, activated_switches=tuple(activated), valid=True)


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

        # 1. Nạp Board và Block an toàn với Adapter Fallback
        self._load_game_data()

        # 2. Khởi tạo thực thể 3D và giao diện 2D
        self.scene_3d_root = Entity()
        self.ui_root = Entity(parent=camera.ui)

        # Thiết lập camera isometric và hệ thống chiếu sáng
        setup_camera(self.board)

        # Hình nền không gian cho màn chơi (ưu tiên ảnh Background)
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
                scale=(w * 1.3, h * 1.3),
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

        # Renderer dựng bàn cờ và BlockRenderer hiển thị khối
        self.renderer = Renderer(self.board, self.scene_3d_root)
        self.block_renderer = BlockRenderer(self.block, self.scene_3d_root)

        # Biến trạng thái trò chơi
        self.steps = 0
        self.is_animating = False
        self.is_game_over = False
        self.is_replaying = False
        self.solution_path = []
        self.solution_step_index = 0
        self.search_result = None

        # 3. Dựng HUD và Result Panel
        self.create_ui()
        self.create_result_panel()

        # 4. Kích hoạt Solver nếu đang ở chế độ 'solve'
        if self.mode == "solve":
            invoke(self.start_solver, delay=0.35)

    def _load_game_data(self):
        """Khởi tạo Board và Block với fallback adapter an toàn."""
        try:
            self.board = Board(self.level_path)
            # Thử truy cập thuộc tính cơ bản để phát hiện NotImplementedError
            _ = self.board.rows
        except Exception:
            self.board = _FallbackBoard(self.level_path)

        try:
            self.block = Block(*self.board.start)
            _ = self.block.orientation
        except Exception:
            self.block = _FallbackBlock(*self.board.start)

        try:
            self.bridge_states = self.board.normalize_bridge_states(self.board.initial_bridge_states)
        except Exception:
            self.bridge_states = getattr(self.board, "initial_bridge_states", ())

    def start_solver(self):
        """Gọi thuật toán giải AI và khởi chạy luồng replay."""
        try:
            from algorithms.solver import solve

            self.search_result = solve(
                self.board,
                self.block,
                self.algorithm,
                self.bridge_states,
            )
        except NotImplementedError:
            self.show_solver_error("Thuật toán solver chưa được triển khai.")
            return
        except Exception as exc:
            self.show_solver_error(f"Lỗi Solver: {exc}")
            return

        if not getattr(self.search_result, "found", False):
            self.show_no_solution()
            return

        # Tìm thấy lời giải, chuẩn bị danh sách action
        self.solution_path = list(getattr(self.search_result, "path", []))
        self.solution_step_index = 0
        self.is_replaying = True

        self.play_next_solution_move()

    def play_next_solution_move(self):
        """Phát lại từng bước trong đường đi lời giải của Solver."""
        if not self.is_replaying or self.is_game_over:
            return

        if self.solution_step_index >= len(self.solution_path):
            self.is_replaying = False
            if not self.is_game_over:
                self.show_win()
            return

        action = self.solution_path[self.solution_step_index]
        self.solution_step_index += 1
        self.try_move(action)

    def update(self):
        """Ursina engine update loop."""
        pass

    def input(self, key):
        """Xử lý sự kiện bàn phím từ người chơi."""
        # Khóa điều khiển khi đang chạy diễn hoạt hoặc đã kết thúc màn
        if self.is_animating or self.is_game_over:
            if key in ("r", "R"):
                self.restart()
            elif key == "escape":
                self.back_to_level_select()
            return

        # Khóa phím lăn tay khi Solver đang tự replay
        if self.mode == "solve":
            if key in ("r", "R"):
                self.restart()
            elif key == "escape":
                self.back_to_level_select()
            return

        # Phím chức năng
        if key in ("r", "R"):
            self.restart()
            return
        elif key == "escape":
            self.back_to_level_select()
            return

        # Ánh xạ phím sang danh sách ALL_ACTIONS chuẩn
        key_map = {
            "w": "UP",
            "up arrow": "UP",
            "s": "DOWN",
            "down arrow": "DOWN",
            "a": "LEFT",
            "left arrow": "LEFT",
            "d": "RIGHT",
            "right arrow": "RIGHT",
            "space": "SWITCH",
            "tab": "SWITCH",
        }

        if key in key_map:
            action = key_map[key]
            # SWITCH chỉ hợp lệ khi khối đang ở trạng thái SPLIT
            if action == "SWITCH":
                ori = getattr(self.block, "orientation", Orientation.STANDING)
                is_split = ori == Orientation.SPLIT or (hasattr(ori, "name") and ori.name == "SPLIT") or ori == 3
                if not is_split:
                    return

            self.try_move(action)

    def try_move(self, action):
        """Gửi action vào Board.transition và kích hoạt diễn hoạt tương ứng."""
        if action not in ALL_ACTIONS:
            return

        self.is_animating = True

        # Gọi Board.transition; TUYỆT ĐỐI KHÔNG tự tính luật lăn hay sửa active_index
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
        """Hoàn tất bước đi hợp lệ, cập nhật trạng thái cầu, HUD và kiểm tra chiến thắng."""
        self.block = transition.block
        self.bridge_states = transition.bridge_states
        self.renderer.refresh_bridge_states(self.bridge_states)

        self.steps += 1
        if hasattr(self, "steps_text") and self.steps_text:
            self.steps_text.text = f"STEPS: {self.steps}"

        self.is_animating = False

        # Kiểm tra chiến thắng
        if self.board.is_win(self.block):
            self.show_win()
        elif self.is_replaying:
            invoke(self.play_next_solution_move, delay=0.12)

    def start_fall(self, transition, direction):
        """Phân loại tình huống rơi khi nước đi không hợp lệ (valid=False)."""
        self.audio_manager.play_lose_sound()

        inv_block = getattr(transition, "block", None) or self.block
        new_bridges = getattr(transition, "bridge_states", self.bridge_states)

        ori_old = getattr(self.block, "orientation", Orientation.STANDING)
        is_old_split = ori_old == Orientation.SPLIT or (hasattr(ori_old, "name") and ori_old.name == "SPLIT") or ori_old == 3

        ori_inv = getattr(inv_block, "orientation", Orientation.STANDING)
        is_inv_standing = ori_inv == Orientation.STANDING or (hasattr(ori_inv, "name") and ori_inv.name == "STANDING") or ori_inv == 0

        # 1. Khối lăn dựng đứng lên ô Fragile sập sàn: lăn lên ô trước rồi mới sập rơi
        if is_inv_standing and hasattr(self.board, "is_fragile") and self.board.is_fragile(*inv_block.pos1):
            self.block_renderer.animate_move(
                self.block,
                inv_block,
                direction,
                on_complete=lambda: self.block_renderer.animate_fall(on_complete=self.show_lose),
            )
            return

        # 2. Rơi trong trạng thái SPLIT
        if is_old_split:
            active_idx = getattr(self.block, "active_index", 0)
            active_cell = inv_block.pos1 if active_idx == 0 else inv_block.pos2

            is_floor = hasattr(self.board, "is_floor") and self.board.is_floor(active_cell[0], active_cell[1], new_bridges)
            if not is_floor:
                # Cube active lăn ra ngoài mép bàn cờ: nghiêng qua mép rồi rơi
                self.block_renderer.animate_tip_and_fall(inv_block, direction, on_complete=self.show_lose)
                return

            # Rơi tại chỗ (ví dụ cầu sập dưới chân cube)
            supported = []
            for cell in (self.block.pos1, self.block.pos2):
                if hasattr(self.board, "is_floor") and self.board.is_floor(cell[0], cell[1], new_bridges):
                    supported.append(cell)
            self.block_renderer.animate_split_fall(supported, on_complete=self.show_lose)
            return

        # 3. Khối nằm nghiêng sụp mép khi một ô còn sàn, một ô ra ngoài vực
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

        # 4. Rơi lật tự do qua mép bàn cờ
        self.block_renderer.animate_tip_and_fall(
            inv_block,
            direction,
            on_complete=self.show_lose,
        )

    def create_ui(self):
        """Dựng giao diện HUD 2D (Header, số bước, nút Back, nút Restart)."""
        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}
        font_bold_kwargs = {"font": FONT_BOLD or FONT_REGULAR} if (FONT_BOLD or FONT_REGULAR) else {}

        # Nút quay về danh sách chọn level
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

        # Tiêu đề Level / Mode
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

        # Số bước di chuyển (Steps)
        self.steps_text = Text(
            parent=self.ui_root,
            text="STEPS: 0",
            origin=(0, 0),
            position=(0, 0.40, -0.05),
            scale=1.15,
            color=PRIMARY,
            **font_bold_kwargs,
        )

        # Nút chơi lại / chạy lại
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

        # Gợi ý điều khiển dưới chân màn hình
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
        """Khởi tạo panel hiển thị kết quả chiến thắng / thất bại / thống kê solver."""
        font_kwargs = {"font": FONT_REGULAR} if FONT_REGULAR else {}
        font_bold_kwargs = {"font": FONT_BOLD or FONT_REGULAR} if (FONT_BOLD or FONT_REGULAR) else {}

        self.result_panel = Entity(parent=self.ui_root, enabled=False, z=-0.10)

        # Tấm nền mờ phủ toàn màn hình
        self.result_overlay = Entity(
            parent=self.result_panel,
            model="quad",
            scale=(camera.aspect_ratio * 2.2, 2.2),
            color=color.rgba32(10, 14, 24, 210),
            position=(0, 0, 0.02),
        )

        # Khung viền panel
        self.result_box = Entity(
            parent=self.result_panel,
            model=Quad(radius=0.04, aspect=RESULT_PANEL_SCALE[0] / RESULT_PANEL_SCALE[1]),
            scale=RESULT_PANEL_SCALE,
            color=RESULT_PANEL_TINT_WIN,
            position=(0, 0, 0.0),
        )

        # Khối cube 3D xoay trang trí trên đỉnh panel
        self.result_cube = RotatingCube(
            parent=self.result_panel,
            position=(0, 0.31, -0.04),
            scale=(0.08, 0.14, 0.08),
        )

        # Tiêu đề kết quả
        self.result_title = Text(
            parent=self.result_panel,
            text="STAGE CLEARED!",
            origin=(0, 0),
            position=(0, 0.185, -0.02),
            scale=1.9,
            color=RESULT_TITLE_COLOR_WIN,
            **font_bold_kwargs,
        )

        # Phụ đề
        self.result_subtitle = Text(
            parent=self.result_panel,
            text="",
            origin=(0, 0),
            position=(0, 0.105, -0.02),
            scale=0.85,
            color=WHITE,
            **font_kwargs,
        )

        # Thông số thống kê chi tiết
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

        # Nút chơi lại
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

        # Nút quay về Level Select
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
        """Cập nhật nội dung văn bản và định dạng cho Result Panel."""
        self.result_title.text = title
        self.result_title.color = title_color
        self.result_subtitle.text = subtitle
        self.result_stats.text = stats
        self.result_stats.scale = stats_scale

    def show_win(self):
        """Hiển thị giao diện chiến thắng kèm số liệu thống kê đầy đủ."""
        self.is_game_over = True
        self.audio_manager.play_win_sound()

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
                f"Steps: {steps}   |   Cost: {cost:.2f}   |   Time: {time_sec:.4f}s\n"
                f"Memory: {mem_mb:.2f} MB   |   Expanded: {expanded}   |   Generated: {generated}\n"
                f"Peak Frontier: {peak}"
            )
            subtitle_msg = f"Solver [{self.algorithm}] executed optimal solution!"
            detailed = True
        else:
            stats_msg = f"Total Steps Taken: {self.steps}"
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
        """Hiển thị thông báo khi khối rơi khỏi bàn cờ."""
        self.is_game_over = True
        self._show_result(
            title="STAGE FAILED!",
            subtitle="The block fell into the abyss.",
            stats=f"Steps reached: {self.steps}",
            outcome="lose",
            detailed=False,
        )

    def show_no_solution(self):
        """Hiển thị thông báo khi Solver không tìm thấy đường đi tới đích."""
        self.is_game_over = True
        self._show_result(
            title="NO SOLUTION FOUND",
            subtitle=f"Solver [{self.algorithm}] searched without finding a path.",
            stats="",
            outcome="neutral",
            detailed=False,
        )

    def show_solver_error(self, message):
        """Hiển thị thông báo khi việc giải thuật toán gặp sự cố / ngoại lệ."""
        self.is_game_over = True
        self._show_result(
            title="SOLVER ERROR",
            subtitle=str(message)[:75],
            stats="",
            outcome="lose",
            detailed=False,
        )

    def _show_result(self, title, subtitle, stats, outcome, detailed=False, show_cube=True):
        """Định hình màu sắc và kích hoạt bảng kết quả."""
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

        # Cập nhật hiển thị khối xoay trang trí
        if hasattr(self, "result_cube") and self.result_cube:
            self.result_cube.enabled = bool(show_cube)

        # Khóa các nút HUD nền khi hiển thị popup kết quả
        if hasattr(self, "back_button") and self.back_button:
            self.back_button.enabled = False
        if hasattr(self, "restart_button") and self.restart_button:
            self.restart_button.enabled = False

        self.result_panel.enabled = True

    def back_to_level_select(self):
        """Dừng âm thanh kết quả và quay trở lại LevelSelectScene."""
        self.audio_manager.stop_result_sounds()
        if self.on_back:
            self.on_back()

    def restart(self):
        """Khôi phục trạng thái ban đầu của màn chơi."""
        self.audio_manager.stop_result_sounds()

        self.steps = 0
        self.is_animating = False
        self.is_game_over = False
        self.is_replaying = False
        self.solution_step_index = 0

        # Khôi phục Block và Cầu
        try:
            self.block = Block(*self.board.start)
        except Exception:
            self.block = _FallbackBlock(*self.board.start)

        try:
            self.bridge_states = self.board.normalize_bridge_states(self.board.initial_bridge_states)
        except Exception:
            self.bridge_states = getattr(self.board, "initial_bridge_states", ())

        self.renderer.refresh_bridge_states(self.bridge_states)

        self.block_renderer.current_block = self.block
        self.block_renderer.update_transform()

        if hasattr(self, "steps_text") and self.steps_text:
            self.steps_text.text = "STEPS: 0"

        if hasattr(self, "result_panel") and self.result_panel:
            self.result_panel.enabled = False

        # Khôi phục hiển thị nút HUD
        if hasattr(self, "back_button") and self.back_button:
            self.back_button.enabled = True
        if hasattr(self, "restart_button") and self.restart_button:
            self.restart_button.enabled = True

        if self.mode == "solve":
            invoke(self.start_solver, delay=0.35)

    def on_destroy(self):
        """Dọn sạch mọi thực thể khi thoát Game Scene."""
        self.is_replaying = False
        self.audio_manager.stop_result_sounds()

        if hasattr(self, "background") and self.background:
            destroy(self.background)
            self.background = None

        if hasattr(self, "scene_3d_root") and self.scene_3d_root:
            destroy(self.scene_3d_root)
            self.scene_3d_root = None

        if hasattr(self, "ui_root") and self.ui_root:
            destroy(self.ui_root)
            self.ui_root = None
