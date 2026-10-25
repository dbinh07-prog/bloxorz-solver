"""IDS solver. Owner: thành viên 4."""

from algorithms.metrics import SearchMetrics
from algorithms.search_result import SearchResult
from algorithms.successor import get_successors
from block import Block
from board import Board
from state import State


def ids(board: Board, start_block: Block, start_bridge_states=None, max_depth: int | None = None) -> SearchResult:
    metrics = SearchMetrics()
    bridge_states = board.normalize_bridge_states(start_bridge_states)
    start_state = State(start_block, bridge_states, parent=None, action=None, cost=0.0)

    if max_depth is None:
        try:
            max_depth = board.estimated_state_count()
        except Exception:
            max_depth = None

    expanded_nodes = 0
    generated_nodes = 0
    peak_frontier = 1

    depth_limit = 0
    while max_depth is None or depth_limit <= max_depth:
        stack = [(start_state, 0)]
        visited_depth = {start_state.key(): 0}
        cutoff_occurred = False

        if len(stack) > peak_frontier:
            peak_frontier = len(stack)

        while stack:
            current_state, depth = stack.pop()

            if visited_depth.get(current_state.key(), depth) < depth:
                continue

            expanded_nodes += 1

            if board.is_win(current_state.block):
                return metrics.result(
                    goal_state=current_state,
                    expanded_nodes=expanded_nodes,
                    generated_nodes=generated_nodes,
                    peak_frontier=peak_frontier,
                )

            if depth < depth_limit:
                successors = get_successors(current_state, board)
                for child in reversed(successors):
                    generated_nodes += 1
                    child_depth = depth + 1
                    child_key = child.key()
                    if child_key not in visited_depth or child_depth < visited_depth[child_key]:
                        visited_depth[child_key] = child_depth
                        stack.append((child, child_depth))

                if len(stack) > peak_frontier:
                    peak_frontier = len(stack)
            else:
                cutoff_occurred = True

        if not cutoff_occurred:
            break

        depth_limit += 1

    return metrics.result(
        goal_state=None,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        peak_frontier=peak_frontier,
    )
