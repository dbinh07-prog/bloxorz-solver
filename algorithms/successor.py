"""Một nguồn successor duy nhất cho mọi solver. Owner: thành viên 4."""

from board import Board
from state import State


def get_successors(state: State, board: Board) -> list[State]:
    """Chỉ dùng board.available_actions/transition/get_action_cost."""
    """Hàm available_actions cho ta biết các hành động có thể đi tiếp."""


    successors=[]
    actions=board.available_actions(state.block)
    for action in actions:
        result=board.transition(state.block,state.bridge_states,action)

        if result.valid:
            current_cost_to_action=board.get_action_cost(result,action)
            current_cost=state.cost+current_cost_to_action

            child_state=State(
                block=result.block,
                bridge_states=result.bridge_states,
                parent=state,
                action=action,
                cost=current_cost
            )
            successors.append(child_state)
    return successors
            
        

