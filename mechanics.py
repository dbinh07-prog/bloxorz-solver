from collections.abc import Mapping
from typing import TYPE_CHECKING

from actions import ROLL_ACTIONS, SWITCH_ACTION
from block import Block, Orientation

if TYPE_CHECKING:
    from board import Board

Cell = tuple[int, int]
BridgeStates = tuple[tuple[str, bool], ...]

UP, DOWN, LEFT, RIGHT = ROLL_ACTIONS

_DELTAS: dict[str, Cell] = {
    UP: (-1, 0),
    DOWN: (1, 0),
    LEFT: (0, -1),
    RIGHT: (0, 1),
}

SWITCH_SOFT = "soft"
SWITCH_HEAVY = "heavy"
SWITCH_SPLIT = "split"
SWITCH_TYPES = (SWITCH_SOFT, SWITCH_HEAVY, SWITCH_SPLIT)

BRIDGE_TOGGLE = "toggle"
BRIDGE_OPEN = "open"
BRIDGE_CLOSE = "close"
BRIDGE_ACTIONS = (BRIDGE_TOGGLE, BRIDGE_OPEN, BRIDGE_CLOSE)

SPLIT_TARGET_COUNT = 2


def _is_split(block: Block) -> bool:
    return block.orientation == Orientation.SPLIT


def _cells(block: Block) -> list[Cell]:


    if block.orientation == Orientation.STANDING:
        return [tuple(block.pos1)]

    return [tuple(block.pos1), tuple(block.pos2)]


def _with_layout(
    block: Block, pos1: Cell, pos2: Cell, orientation: Orientation, active_index: int = 0
) -> Block:


    new_block = block.copy()
    new_block.pos1 = (int(pos1[0]), int(pos1[1]))
    new_block.pos2 = (int(pos2[0]), int(pos2[1]))
    new_block.orientation = orientation
    new_block.active_index = active_index

    return new_block


def _to_cell(value) -> Cell:


    row, col = value

    return int(row), int(col)


def _bridge_dict(board: "Board", bridge_states) -> dict[str, bool]:


    if bridge_states is None:
        bridge_states = getattr(board, "initial_bridge_states", ())

    if isinstance(bridge_states, Mapping):
        return {str(k): bool(v) for k, v in bridge_states.items()}

    return {str(k): bool(v) for k, v in bridge_states}


def _bridge_tuple(states: Mapping[str, bool]) -> BridgeStates:


    return tuple(sorted((k, bool(v)) for k, v in states.items()))


def _pressed_switches(board: "Board", block: Block | None) -> dict[str, dict]:

    if block is None:
        return {}

    standing = block.orientation == Orientation.STANDING
    pressed: dict[str, dict] = {}

    for row, col in _cells(block):

        if not board.is_inside(row, col):
            continue
        switch = board.get_switch(row, col)

        if switch is None:
            continue
        kind = switch.get("type")

        if kind not in SWITCH_TYPES:
            raise ValueError(f"Unknown switch type: {kind!r}")

        if kind == SWITCH_SOFT or standing:
            pressed[str(switch["id"])] = switch

    return pressed


def _apply_bridge_action(states: dict[str, bool], switch: Mapping) -> None:


    bridge_ids = switch.get("bridges", ()) or ()

    if not bridge_ids:
        return

    action = switch.get("action", BRIDGE_TOGGLE)

    if action not in BRIDGE_ACTIONS:
        raise ValueError(f"Unknown bridge action: {action!r}")

    for bridge_id in bridge_ids:

        bridge_id = str(bridge_id)

        if bridge_id not in states:
            raise ValueError(f"Switch {switch.get('id')!r} references unknown bridge {bridge_id!r}")

        if action == BRIDGE_TOGGLE:
            states[bridge_id] = not states[bridge_id]

        else:
            states[bridge_id] = action == BRIDGE_OPEN


def move_split(block: Block, action: str) -> Block:


    if not _is_split(block):
        raise ValueError("move_split requires a SPLIT block")

    if block.active_index not in (0, 1):
        raise ValueError(f"Invalid active_index: {block.active_index!r}")

    pos1, pos2 = tuple(block.pos1), tuple(block.pos2)

    if action == SWITCH_ACTION:
        return _with_layout(block, pos1, pos2, Orientation.SPLIT, 1 - block.active_index)

    if action not in _DELTAS:
        raise ValueError(f"Unknown action: {action!r}")

    d_row, d_col = _DELTAS[action]

    if block.active_index == 0:
        pos1 = (pos1[0] + d_row, pos1[1] + d_col)

    else:
        pos2 = (pos2[0] + d_row, pos2[1] + d_col)

    return _with_layout(block, pos1, pos2, Orientation.SPLIT, block.active_index)


def is_special_supported(board: "Board", block: Block) -> bool:


    if block.orientation != Orientation.STANDING:
        return True

    row, col = tuple(block.pos1)

    if not board.is_inside(row, col):
        return True

    return not board.is_fragile(row, col)


def split_block(block: Block, targets: tuple[tuple[int, int], tuple[int, int]]) -> Block:


    if targets is None or len(targets) != SPLIT_TARGET_COUNT:
        raise ValueError(f"Split switch needs exactly {SPLIT_TARGET_COUNT} targets")

    first, second = _to_cell(targets[0]), _to_cell(targets[1])

    if first == second:

        raise ValueError("Split targets must be two distinct cells")

    return _with_layout(block, first, second, Orientation.SPLIT, 0)


def merge_if_adjacent(block: Block) -> Block:


    if not _is_split(block):
        return block.copy()

    (r1, c1), (r2, c2) = tuple(block.pos1), tuple(block.pos2)

    if r1 == r2 and abs(c1 - c2) == 1:

        left, right = sorted(((r1, c1), (r2, c2)))

        return _with_layout(block, left, right, Orientation.HORIZONTAL, 0)

    if c1 == c2 and abs(r1 - r2) == 1:

        top, bottom = sorted(((r1, c1), (r2, c2)))

        return _with_layout(block, top, bottom, Orientation.VERTICAL, 0)

    return block.copy()


def apply_special_tiles(
    board: "Board", old_block: Block, moved_block: Block, bridge_states: tuple
) -> tuple[Block, tuple[tuple[str, bool], ...], tuple[str, ...]]:
    states = _bridge_dict(board, bridge_states)

    before = _pressed_switches(board, old_block)
    after = _pressed_switches(board, moved_block)
    newly_ids = sorted(set(after) - set(before))

    result_block = moved_block.copy()

    for switch_id in newly_ids:
        switch = after[switch_id]
        _apply_bridge_action(states, switch)

        if switch["type"] == SWITCH_SPLIT:
            result_block = split_block(result_block, switch.get("targets"))

    if _is_split(result_block):
        result_block = merge_if_adjacent(result_block)

    return result_block, _bridge_tuple(states), tuple(newly_ids)
