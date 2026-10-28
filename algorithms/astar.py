from heapq import heappop, heappush
from itertools import count

from algorithms.metrics import SearchMetrics
from algorithms.search_result import SearchResult
from algorithms.successor import get_successors
from block import Block
from board import Board
from state import State


def astar(board: Board, start_block: Block, start_bridge_states=None) -> SearchResult:
    measurement = SearchMetrics()
    start_state = State(start_block, board.normalize_bridge_states(start_bridge_states))
    visited_count = produced_count = largest_queue = 0

    def make_report(destination=None):
        return measurement.result(
            goal_state=destination,
            expanded_nodes=visited_count,
            generated_nodes=produced_count,
            peak_frontier=largest_queue,
        )

    if not board.is_valid_block(start_state.block, start_state.bridge_states):
        return make_report()

    start_estimate = board.heuristic(start_state.block)
    produced_count = 1
    if start_estimate == float("inf"):
        return make_report()

    ticket = count()
    pending_states = []
    heappush(pending_states, (start_estimate, start_estimate, next(ticket), start_state))
    lowest_cost = {start_state.key(): start_state.cost}
    largest_queue = 1

    while pending_states:
        selected = heappop(pending_states)[3]
        if selected.cost != lowest_cost[selected.key()]:
            continue


        visited_count += 1
        if board.is_win(selected.block):
            return make_report(selected)

        for candidate in get_successors(selected, board):
            produced_count += 1
            if candidate.cost <= selected.cost:
                raise ValueError("A* requires strictly positive action costs")
            candidate_key = candidate.key()
            known_cost = lowest_cost.get(candidate_key)
            if known_cost is not None and known_cost <= candidate.cost:
                continue


            lowest_cost[candidate_key] = candidate.cost
            remaining_estimate = board.heuristic(candidate.block)
            if remaining_estimate == float("inf"):
                continue
            estimated_total = candidate.cost + remaining_estimate
            heappush(pending_states, (estimated_total, remaining_estimate, next(ticket), candidate))

        largest_queue = max(largest_queue, len(pending_states))

    return make_report()
