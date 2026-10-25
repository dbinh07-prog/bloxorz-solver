import unittest
from algorithms.solver import solve
from block import Block
from board import Board


class SolverTests(unittest.TestCase):

    def replay(self, board, path):
        current_block = Block(*board.start)
        bridge_states = board.initial_bridge_states

        for action in path:
            current_action = board.transition(current_block, bridge_states, action)
            self.assertTrue(current_action.valid, f"Nước đi {action} không hợp lệ hoặc làm rơi khối")
            block = current_action.block
            bridge_states = current_action.bridge_states
        self.assertTrue(board.is_win(block), "Khối chưa đứng thẳng trên ô đích")

        


    def test_all_algorithms_solve_basic_and_advanced_levels(self):
        algorithms = ["BFS", "IDS", "UCS", "ASTAR"]
        board = Board("maps/example_basic.json")
        start_block = Block(*board.start)
        for algo in algorithms:
            with self.subTest(algorithm=algo):
                res = solve(board, start_block, algo)
                self.assertTrue(res.found_solution, f"{algo} không tìm ra lời giải!")
                self.assertIsNotNone(res.path)
                self.replay(board, res.path)

    def test_solver_can_change_the_active_split_cube(self):
        

    def test_ucs_uses_non_uniform_cost(self):
        raise NotImplementedError
