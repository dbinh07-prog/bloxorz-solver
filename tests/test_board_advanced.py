import json
import tempfile
import unittest
from pathlib import Path

import mechanics
from block import Block, Orientation

S, H, V, SP = (
    Orientation.STANDING,
    Orientation.HORIZONTAL,
    Orientation.VERTICAL,
    Orientation.SPLIT,
)


class FakeBlock:

    def __init__(self, pos1, pos2=None, orientation=S, active_index=0):
        self.pos1 = tuple(pos1)
        self.pos2 = tuple(pos2) if pos2 is not None else tuple(pos1)
        self.orientation = orientation
        self.active_index = active_index

    def copy(self):
        return FakeBlock(self.pos1, self.pos2, self.orientation, self.active_index)

    def snapshot(self):
        return (self.orientation, self.pos1, self.pos2, self.active_index)


class FakeBoard:

    def __init__(self, grid, switches=(), bridges=None):

        self.grid = [list(row) for row in grid]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.switches = {tuple(sw["position"]): sw for sw in switches}
        self.initial_bridge_states = tuple(sorted((bridges or {}).items()))

    def is_inside(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_fragile(self, row, col):
        return self.grid[row][col] == "F"

    def get_switch(self, row, col):
        return self.switches.get((row, col))


def soft(sid, pos, bridges=(), action="toggle"):
    return {"id": sid, "position": list(pos), "type": "soft",
            "bridges": list(bridges), "action": action}


def heavy(sid, pos, bridges=(), action="toggle"):
    return {"id": sid, "position": list(pos), "type": "heavy",
            "bridges": list(bridges), "action": action}


def split(sid, pos, targets, bridges=(), action="toggle"):
    return {"id": sid, "position": list(pos), "type": "split",
            "bridges": list(bridges), "action": action,
            "targets": [list(t) for t in targets]}


GRID_5X7 = ["." * 7] * 5


class MechanicsUnitTests(unittest.TestCase):


    def test_move_split_moves_only_active_cube_without_mutating_input(self):

        block = FakeBlock((0, 0), (3, 3), SP, active_index=0)
        before = block.snapshot()

        moved = mechanics.move_split(block, "RIGHT")
        self.assertEqual(moved.snapshot(), (SP, (0, 1), (3, 3), 0))

        block2 = FakeBlock((0, 0), (3, 3), SP, active_index=1)
        moved2 = mechanics.move_split(block2, "UP")
        self.assertEqual(moved2.snapshot(), (SP, (0, 0), (2, 3), 1))

        self.assertEqual(block.snapshot(), before)
        self.assertIsNot(moved, block)


    def test_move_split_switch_action_swaps_active_cube(self):

        block = FakeBlock((0, 0), (3, 3), SP, active_index=0)
        swapped = mechanics.move_split(block, "SWITCH")
        self.assertEqual(swapped.snapshot(), (SP, (0, 0), (3, 3), 1))
        self.assertEqual(mechanics.move_split(swapped, "SWITCH").active_index, 0)
        self.assertEqual(block.active_index, 0)


    def test_move_split_rejects_non_split_block_and_unknown_action(self):

        with self.assertRaises(ValueError):
            mechanics.move_split(FakeBlock((1, 1)), "UP")
        with self.assertRaises(ValueError):
            mechanics.move_split(FakeBlock((0, 0), (3, 3), SP), "JUMP")
        with self.assertRaises(ValueError):
            mechanics.move_split(FakeBlock((0, 0), (3, 3), SP), "w")


    def test_split_block_creates_two_cubes_with_first_active(self):

        block = FakeBlock((2, 2))
        result = mechanics.split_block(block, ([0, 1], (4, 5)))
        self.assertEqual(result.snapshot(), (SP, (0, 1), (4, 5), 0))
        self.assertEqual(block.snapshot(), (S, (2, 2), (2, 2), 0))


    def test_split_block_rejects_invalid_targets(self):

        block = FakeBlock((2, 2))
        with self.assertRaises(ValueError):
            mechanics.split_block(block, ((0, 0),))
        with self.assertRaises(ValueError):
            mechanics.split_block(block, ((1, 1), (1, 1)))
        with self.assertRaises(ValueError):
            mechanics.split_block(block, None)


    def test_merge_horizontal_normalizes_left_cell_first(self):

        block = FakeBlock((2, 4), (2, 3), SP, active_index=1)
        merged = mechanics.merge_if_adjacent(block)
        self.assertEqual(merged.snapshot(), (H, (2, 3), (2, 4), 0))
        self.assertEqual(block.orientation, SP)


    def test_merge_vertical_normalizes_top_cell_first(self):

        merged = mechanics.merge_if_adjacent(FakeBlock((3, 1), (2, 1), SP))
        self.assertEqual(merged.snapshot(), (V, (2, 1), (3, 1), 0))


    def test_no_merge_when_diagonal_or_far(self):

        for other in ((1, 1), (0, 2), (2, 0)):
            block = FakeBlock((0, 0), other, SP, active_index=1)
            result = mechanics.merge_if_adjacent(block)
            self.assertEqual(result.snapshot(), block.snapshot())
            self.assertIsNot(result, block)


    def test_merge_returns_copy_for_non_split_block(self):

        block = FakeBlock((1, 1), (1, 2), H)
        result = mechanics.merge_if_adjacent(block)
        self.assertEqual(result.snapshot(), block.snapshot())
        self.assertIsNot(result, block)


    def test_fragile_rejects_standing_but_supports_lying_and_cube(self):

        board = FakeBoard(["....", ".F..", "...."])
        self.assertFalse(mechanics.is_special_supported(board, FakeBlock((1, 1))))
        self.assertTrue(mechanics.is_special_supported(board, FakeBlock((1, 1), (1, 2), H)))
        self.assertTrue(mechanics.is_special_supported(board, FakeBlock((0, 1), (1, 1), V)))
        self.assertTrue(
            mechanics.is_special_supported(board, FakeBlock((1, 1), (2, 3), SP))
        )
        self.assertTrue(mechanics.is_special_supported(board, FakeBlock((0, 0))))


    def test_fragile_check_outside_board_does_not_raise(self):

        board = FakeBoard(["F"])
        self.assertTrue(mechanics.is_special_supported(board, FakeBlock((-1, 5))))


    def test_soft_switch_triggered_by_lying_block(self):

        board = FakeBoard(GRID_5X7, [soft("s1", (1, 2), ["b1"])], {"b1": False})
        old = FakeBlock((1, 0))
        moved = FakeBlock((1, 1), (1, 2), H)
        block, states, activated = mechanics.apply_special_tiles(
            board, old, moved, (("b1", False),)
        )
        self.assertEqual(activated, ("s1",))
        self.assertEqual(states, (("b1", True),))
        self.assertEqual(block.snapshot(), moved.snapshot())


    def test_soft_switch_triggered_by_single_split_cube(self):

        board = FakeBoard(GRID_5X7, [soft("s1", (0, 1), ["b1"])], {"b1": False})
        old = FakeBlock((0, 0), (4, 6), SP)
        moved = mechanics.move_split(old, "RIGHT")
        _, states, activated = mechanics.apply_special_tiles(
            board, old, moved, (("b1", False),)
        )
        self.assertEqual(activated, ("s1",))
        self.assertEqual(states, (("b1", True),))


    def test_heavy_switch_ignores_lying_block_and_split_cube(self):

        board = FakeBoard(GRID_5X7, [heavy("h1", (2, 2), ["b1"])], {"b1": False})
        cases = (
            (FakeBlock((2, 0)), FakeBlock((2, 1), (2, 2), H)),
            (FakeBlock((0, 2)), FakeBlock((1, 2), (2, 2), V)),
            (FakeBlock((2, 1), (4, 6), SP), FakeBlock((2, 2), (4, 6), SP)),
        )
        for old, moved in cases:
            with self.subTest(moved=moved.snapshot()):
                _, states, activated = mechanics.apply_special_tiles(
                    board, old, moved, (("b1", False),)
                )
                self.assertEqual(activated, ())
                self.assertEqual(states, (("b1", False),))


    def test_heavy_switch_triggered_by_standing_block(self):

        board = FakeBoard(GRID_5X7, [heavy("h1", (2, 3), ["b1"])], {"b1": False})
        _, states, activated = mechanics.apply_special_tiles(
            board, FakeBlock((2, 1), (2, 2), H), FakeBlock((2, 3)), (("b1", False),)
        )
        self.assertEqual(activated, ("h1",))
        self.assertEqual(states, (("b1", True),))


    def test_toggle_flips_each_trigger(self):

        board = FakeBoard(GRID_5X7, [soft("s1", (2, 3), ["b1"])], {"b1": False})
        states = (("b1", False),)
        for expected in (True, False, True):
            _, states, _ = mechanics.apply_special_tiles(
                board, FakeBlock((2, 1), (2, 2), H), FakeBlock((2, 3)), states
            )
            self.assertEqual(states, (("b1", expected),))


    def test_permanent_open_and_close_set_fixed_state(self):

        board = FakeBoard(
            GRID_5X7,
            [soft("on", (0, 0), ["b1"], "open"), soft("off", (4, 6), ["b1"], "close")],
            {"b1": False},
        )
        stand_on = FakeBlock((0, 0))
        stand_off = FakeBlock((4, 6))
        far = FakeBlock((2, 3))
        for initial in (False, True):
            _, states, _ = mechanics.apply_special_tiles(
                board, far, stand_on, (("b1", initial),)
            )
            self.assertEqual(states, (("b1", True),))
            _, states, _ = mechanics.apply_special_tiles(
                board, far, stand_off, (("b1", initial),)
            )
            self.assertEqual(states, (("b1", False),))


    def test_switch_not_retriggered_while_still_pressed(self):

        board = FakeBoard(GRID_5X7, [soft("s1", (0, 0), ["b1"])], {"b1": False})
        old = FakeBlock((0, 0), (4, 4), SP, active_index=0)
        swapped = mechanics.move_split(old, "SWITCH")
        _, states, activated = mechanics.apply_special_tiles(
            board, old, swapped, (("b1", True),)
        )
        self.assertEqual((states, activated), ((("b1", True),), ()))
        moved = mechanics.move_split(swapped, "LEFT")
        _, states, activated = mechanics.apply_special_tiles(
            board, swapped, moved, (("b1", True),)
        )
        self.assertEqual((states, activated), ((("b1", True),), ()))


    def test_switch_controls_multiple_bridges_and_output_is_sorted(self):

        board = FakeBoard(
            GRID_5X7, [soft("s1", (2, 3), ["b2", "b1"])], {"b2": True, "b1": False}
        )
        input_states = {"b2": True, "b1": False}
        _, states, _ = mechanics.apply_special_tiles(
            board, FakeBlock((2, 1), (2, 2), H), FakeBlock((2, 3)), input_states
        )
        self.assertEqual(states, (("b1", True), ("b2", False)))
        self.assertEqual(input_states, {"b2": True, "b1": False})


    def test_none_bridge_states_uses_initial_states(self):

        board = FakeBoard(GRID_5X7, [soft("s1", (2, 3), ["b1"])], {"b1": True})
        _, states, _ = mechanics.apply_special_tiles(
            board, FakeBlock((2, 1), (2, 2), H), FakeBlock((2, 3)), None
        )
        self.assertEqual(states, (("b1", False),))


    def test_invalid_switch_metadata_raises(self):

        bad_action = FakeBoard(GRID_5X7, [soft("s1", (2, 3), ["b1"], "flip")], {"b1": False})
        bad_bridge = FakeBoard(GRID_5X7, [soft("s1", (2, 3), ["bx"])], {"b1": False})
        bad_type = FakeBoard(
            GRID_5X7, [{"id": "s1", "position": [2, 3], "type": "magic"}], {"b1": False}
        )
        for board in (bad_action, bad_bridge, bad_type):
            with self.assertRaises(ValueError):
                mechanics.apply_special_tiles(
                    board, FakeBlock((0, 0)), FakeBlock((2, 3)), (("b1", False),)
                )


    def test_split_switch_requires_standing_and_teleports(self):

        board = FakeBoard(GRID_5X7, [split("x1", (2, 1), [(0, 0), (0, 4)])])
        lying = FakeBlock((2, 1), (2, 2), H)
        block, _, activated = mechanics.apply_special_tiles(
            board, FakeBlock((2, 3)), lying, ()
        )
        self.assertEqual((block.orientation, activated), (H, ()))


        moved = FakeBlock((2, 1))
        block, states, activated = mechanics.apply_special_tiles(board, lying, moved, ())
        self.assertEqual(activated, ("x1",))
        self.assertEqual(states, ())
        self.assertEqual(block.snapshot(), (SP, (0, 0), (0, 4), 0))
        self.assertEqual(moved.snapshot(), (S, (2, 1), (2, 1), 0))


    def test_split_cubes_merge_when_adjacent(self):

        board = FakeBoard(GRID_5X7)
        block = FakeBlock((0, 0), (0, 3), SP, active_index=0)
        for _ in range(2):
            moved = mechanics.move_split(block, "RIGHT")
            block, _, _ = mechanics.apply_special_tiles(board, block, moved, ())
        self.assertEqual(block.snapshot(), (H, (0, 2), (0, 3), 0))


    def test_split_cube_presses_soft_switch_then_merges_later(self):

        board = FakeBoard(GRID_5X7, [soft("s1", (1, 3), ["b1"])], {"b1": False})
        old = FakeBlock((2, 2), (0, 3), SP, active_index=0)
        moved = mechanics.move_split(mechanics.move_split(old, "SWITCH"), "DOWN")
        block, states, activated = mechanics.apply_special_tiles(
            board, old, moved, (("b1", False),)
        )
        self.assertEqual(activated, ("s1",))
        self.assertEqual(states, (("b1", True),))
        self.assertEqual(block.snapshot(), (SP, (2, 2), (1, 3), 1))

        moved = mechanics.move_split(block, "DOWN")
        block, _, _ = mechanics.apply_special_tiles(board, block, moved, states)
        self.assertEqual(block.snapshot(), (H, (2, 2), (2, 3), 0))


def _core_ready() -> bool:

    try:
        from board import Board

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "probe.json"
            path.write_text(json.dumps({
                "grid": ["...."], "start": [0, 0], "goal": [0, 3],
                "bridges": {}, "switches": [],
            }), encoding="utf-8")
            board = Board(path)
            board.transition(Block(0, 0), board.initial_bridge_states, "RIGHT")
    except NotImplementedError:
        return False
    return True


CORE_READY = _core_ready()


class TemporaryBoardTestCase(unittest.TestCase):


    def setUp(self):

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)


    def make_board(self, data):

        from board import Board

        payload = {"bridges": {}, "switches": [], **data}
        path = Path(self._tmp.name) / "map.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return Board(path)


    def step(self, board, block, states, action):
        return board.transition(block, states, action)


@unittest.skipUnless(CORE_READY, "Chờ Block/Board (thành viên 1) hoàn thành")
class BoardAdvancedTileTests(TemporaryBoardTestCase):

    def test_half_outside_board_is_invalid_without_index_error(self):

        board = self.make_board({"grid": ["...", "...", "..."], "start": [0, 1], "goal": [2, 2]})
        result = self.step(board, Block(0, 1), board.initial_bridge_states, "UP")
        self.assertFalse(result.valid)
        result = self.step(board, Block(1, 2), board.initial_bridge_states, "RIGHT")
        self.assertFalse(result.valid)


    def test_fragile_tile_rejects_standing_but_supports_lying(self):

        board = self.make_board({
            "grid": ["......", "..F...", "......"], "start": [1, 0], "goal": [2, 5],
        })
        states = board.initial_bridge_states
        lying = self.step(board, Block(1, 0), states, "RIGHT")
        self.assertTrue(lying.valid)
        self.assertEqual(lying.block.orientation, H)
        self.assertTrue(self.step(board, Block(0, 2), states, "DOWN").valid)

        approach = self.step(board, Block(1, 5), states, "LEFT")
        self.assertTrue(approach.valid)
        on_fragile = self.step(board, approach.block, states, "LEFT")
        self.assertFalse(on_fragile.valid)


    def test_soft_switch_opens_bridge_when_any_part_presses_it(self):

        board = self.make_board({
            "grid": ["......", "......", "......"], "start": [1, 0], "goal": [2, 5],
            "bridges": {"b1": {"cells": [[0, 5]], "initial_open": False}},
            "switches": [soft("s1", (1, 2), ["b1"])],
        })
        result = self.step(board, Block(1, 0), board.initial_bridge_states, "RIGHT")

        self.assertTrue(result.valid)
        self.assertEqual(result.activated_switches, ("s1",))
        self.assertEqual(result.bridge_states, (("b1", True),))


    def test_heavy_switch_requires_standing(self):

        board = self.make_board({
            "grid": ["......", "......", "......"], "start": [1, 0], "goal": [2, 5],
            "bridges": {"b1": {"cells": [[0, 5]], "initial_open": False}},
            "switches": [heavy("h1", (1, 3), ["b1"])],
        })
        states = board.initial_bridge_states
        across = self.step(board, Block(1, 1), states, "RIGHT")

        self.assertTrue(across.valid)
        self.assertEqual(across.activated_switches, ())
        self.assertEqual(across.bridge_states, (("b1", False),))

        lying = self.step(board, Block(1, 0), states, "RIGHT")
        standing = self.step(board, lying.block, lying.bridge_states, "RIGHT")

        self.assertTrue(standing.valid)
        self.assertEqual(standing.activated_switches, ("h1",))
        self.assertEqual(standing.bridge_states, (("b1", True),))


    def test_split_switch_teleports_and_cubes_rejoin(self):

        board = self.make_board({
            "grid": ["." * 7] * 5, "start": [2, 4], "goal": [0, 0],
            "bridges": {"b1": {"cells": [[4, 6]], "initial_open": False}},
            "switches": [
                split("x1", (2, 1), [(0, 0), (0, 3)]),
                soft("s1", (0, 1), ["b1"]),
            ],
        })
        states = board.initial_bridge_states
        lying = self.step(board, Block(2, 4), states, "LEFT")
        result = self.step(board, lying.block, lying.bridge_states, "LEFT")

        self.assertTrue(result.valid)
        self.assertIn("x1", result.activated_switches)

        block = result.block

        self.assertEqual(block.orientation, SP)
        self.assertEqual({tuple(block.pos1), tuple(block.pos2)}, {(0, 0), (0, 3)})
        self.assertFalse(board.is_win(block))
        self.assertIn("SWITCH", board.available_actions(block))

        swapped = self.step(board, block, result.bridge_states, "SWITCH")

        self.assertTrue(swapped.valid)
        self.assertNotEqual(swapped.block.active_index, block.active_index)

        back = self.step(board, swapped.block, swapped.bridge_states, "SWITCH")

        self.assertEqual(back.block.active_index, block.active_index)

        if tuple(block.get_active_cell()) != (0, 0):
            block = swapped.block

        r1 = self.step(board, block, result.bridge_states, "RIGHT")

        self.assertTrue(r1.valid)
        self.assertEqual(r1.activated_switches, ("s1",))
        self.assertEqual(r1.bridge_states, (("b1", True),))

        r2 = self.step(board, r1.block, r1.bridge_states, "RIGHT")

        self.assertTrue(r2.valid)
        self.assertEqual(r2.block.orientation, H)
        self.assertEqual((tuple(r2.block.pos1), tuple(r2.block.pos2)), ((0, 2), (0, 3)))


    def test_switch_closing_bridge_under_block_makes_it_fall(self):

        board = self.make_board({
            "grid": ["....", "....", "...."], "start": [1, 0], "goal": [2, 3],
            "bridges": {"b1": {"cells": [[1, 2]], "initial_open": True}},
            "switches": [soft("s1", (1, 1), ["b1"], "close")],
        })
        result = self.step(board, Block(1, 0), board.initial_bridge_states, "RIGHT")
        self.assertFalse(result.valid)


    def test_transition_does_not_mutate_inputs(self):

        board = self.make_board({
            "grid": ["." * 7] * 5, "start": [2, 1], "goal": [4, 6],
            "bridges": {"b1": {"cells": [[4, 6]], "initial_open": False}},
            "switches": [split("x1", (2, 1), [(0, 0), (0, 4)], ["b1"])],
        })

        block = Block(2, 4)
        states = board.initial_bridge_states
        key_before = block.state_key()
        lying = self.step(board, block, states, "LEFT")

        self.assertEqual(block.state_key(), key_before)

        lying_key = lying.block.state_key()
        result = self.step(board, lying.block, lying.bridge_states, "LEFT")

        self.assertEqual(lying.block.state_key(), lying_key)
        self.assertEqual(states, (("b1", False),))
        self.assertEqual(result.bridge_states, (("b1", True),))


if __name__ == "__main__":
    unittest.main()
