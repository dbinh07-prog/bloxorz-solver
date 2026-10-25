"""BFS solver. Owner: thành viên 4."""

from collections import deque
from algorithms.search_result import SearchResult
from block import Block
from board import Board
from state import State
from algorithms.metrics import SearchMetrics
from algorithms.successor import get_successors


def bfs(board: Board, start_block: Block, start_bridge_states=None) -> SearchResult:
    
    current_metrics=SearchMetrics()
    bridge_states=board.normalize_bridge_states(start_bridge_states)
    start_state=State(start_block,bridge_states,parent=None,action=None,cost=0.0)
    queue=deque([start_state])
    expanded_nodes=0
    generated_nodes=0
    peak_frontier=1
    visited={start_state.key()}
    

    while queue:
        current_state=queue.popleft()
        expanded_nodes+=1
        if board.is_win(current_state.block):
            return current_metrics.result(
                goal_state= current_state,
                expanded_nodes=expanded_nodes,
                generated_nodes=generated_nodes,
                peak_frontier=peak_frontier
            )
        
        successors=get_successors(current_state, board)

        for successor_case in successors:
            generated_nodes+=1
            if successor_case.key() not in visited:
                queue.append(successor_case)
                visited.add(successor_case.key())
            
                if len(queue)>peak_frontier:
                    peak_frontier=len(queue)
        
    return current_metrics.result(
        goal_state=None,
        expanded_nodes=expanded_nodes,
        generated_nodes=generated_nodes,
        peak_frontier=peak_frontier
    )
        



    

    
            
            



    
    
