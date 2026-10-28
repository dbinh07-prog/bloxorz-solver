import heapq
from algorithms.search_result import SearchResult
from block import Block
from board import Board
from state import State
from algorithms.successor import get_successors
from algorithms.metrics import SearchMetrics
from algorithms.search_result import SearchResult

def ucs(board: Board, start_block: Block, start_bridge_states=None) -> SearchResult:

    metrics = SearchMetrics()
    bridge_states=board.normalize_bridge_states(start_bridge_states)
    start_state = State(start_block, bridge_states, parent=None, action=None,cost=0.0)
    visited=set()
    track=0
    priority_queue = [(start_state.cost, track ,start_state)]
    best_cost={start_state.key() : start_state.cost}
    expanded_nodes=0
    generated_nodes=1
    peak_frontier=1

    if not board.is_valid_block(start_state.block, start_state.bridge_states):
        return metrics.result()

    while priority_queue:
        current_cost, current_track, current_state = heapq.heappop(priority_queue)
        if current_state.key() in visited:
            continue

        expanded_nodes+=1
        visited.add(current_state.key())
        if board.is_win(current_state.block):
            return metrics.result(
                goal_state=current_state,
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                peak_frontier=peak_frontier
            )

        successors = get_successors(current_state, board)
        for child in successors:
            generated_nodes+=1
            if child.key() not in visited:
                min_dist = child.cost
                if child.key() not in best_cost:
                    best_cost[child.key()] = min_dist
                    track+=1
                    heapq.heappush(priority_queue, (min_dist, track, child))
                else:
                    if min_dist < best_cost[child.key()]:
                        best_cost[child.key()] = min_dist
                        track+=1
                        heapq.heappush(priority_queue,(min_dist, track, child))
                if len(priority_queue) > peak_frontier:
                    peak_frontier = len(priority_queue)

    return metrics.result(
        goal_state=None,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        peak_frontier=peak_frontier
    )
