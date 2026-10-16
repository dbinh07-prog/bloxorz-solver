"""Một nguồn successor duy nhất cho mọi solver. Owner: thành viên 4."""

from board import Board
from state import State


def get_successors(state: State, board: Board) -> list[State]:
    """Chỉ dùng board.available_actions/transition/get_action_cost."""
    raise NotImplementedError
