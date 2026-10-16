"""API gọi solver từ GUI/benchmark. Owner: thành viên 4."""

from algorithms.search_result import SearchResult
from block import Block
from board import Board


def solve(
    board: Board,
    start_block: Block,
    algorithm_name: str,
    start_bridge_states=None,
) -> SearchResult:
    """Nhận BFS, IDS, UCS, ASTAR (và alias A*); lỗi tên thì ValueError."""
    raise NotImplementedError
