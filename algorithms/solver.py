"""API gọi solver từ GUI/benchmark. Owner: thành viên 4."""

from algorithms.search_result import SearchResult
from block import Block
from board import Board
from algorithms.bfs import bfs
from algorithms.ids import ids
from algorithms.astar import astar
from algorithms.ucs import ucs


def solve(
    board: Board,
    start_block: Block,
    algorithm_name: str,
    start_bridge_states=None,
) -> SearchResult:
    """Nhận BFS, IDS, UCS, ASTAR (và alias A*); lỗi tên thì ValueError."""

    algorithms={
        "BFS":bfs,
        "IDS":ids,
        "ASTAR":astar,
        "A*": astar,
        "UCS":ucs
    }

    algorithm_name_input = algorithm_name.upper().strip()
    if algorithm_name_input not in algorithms:
        raise ValueError("Algorithm Name is not valid")

    return algorithms[algorithm_name_input](board, start_block, start_bridge_states)
