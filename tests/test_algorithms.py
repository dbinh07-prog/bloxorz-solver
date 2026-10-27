import unittest
from algorithms.solver import solve
from block import Block
from board import Board


class SolverTests(unittest.TestCase):

    def replay(self, board, path):
        current_block = Block(*board.start)
        current_bridge_states = board.initial_bridge_states
        for action in path:
            step = board.transition(current_block, current_bridge_states, action)

            # Kiểm tra tính hợp lệ của nước đi. 
            self.assertTrue(step.valid, f"Nước đi {action} không hợp lệ")
            current_block = step.block
            current_bridge_states = step.bridge_states
        
        self.assertTrue(board.is_win(current_block), "Khối chưa khớp với vị trí đích")


    def test_all_algorithms_solve_basic_and_advanced_levels(self):
        algorithms = ["BFS","IDS","ASTAR","UCS"]
        testMaps = [
            "maps/example_basic.json",
            "maps/level_1.json",
            "maps/level_7.json",
        ]

        for testMap in testMaps:
            board = Board(testMap)
            start_block = Block(*board.start)

            for algo in algorithms:
                with self.subTest(map = testMap, algorithm = algo):
                    res = solve(board, start_block, algo)
                    self.assertTrue(res.found, f"{algo} không giải được {testMap}")
                    self.assertIsNotNone(res.path)
                    self.replay(board, res.path)

        

    def test_solver_can_change_the_active_split_cube(self):
        map_test = Board("maps/level_11.json")
        start_block = Block(*map_test.start)
        res = solve(map_test, start_block, "ASTAR")

        self.assertTrue(res.found, "Solver không giải được map có chế độ tách khối")
        self.assertIsNotNone(res.path)

        self.assertIn(
            "SWITCH",
            res.path,
            "Lời giải tìm được không chứa hành động 'SWITCH'"   
        )

        self.replay(map_test, res.path)


    def test_ucs_uses_non_uniform_cost(self):
        map_test = Board("maps/level_4.json")
        start_block = Block(*map_test.start)

        bfs_result = solve(map_test, start_block, "BFS")
        ucs_result = solve(map_test, start_block, "UCS")
        self.assertTrue(bfs_result.found, "BFS không tìm ra lời giải")
        self.assertTrue(ucs_result.found, "UCS không tìm ra lời giải")

        self.assertLessEqual(
            ucs_result.solution_cost,
            bfs_result.solution_cost,
            "Chi phí của UCS phải nhỏ hơn hoặc bằng BFS"
        )
        
        self.replay(map_test, ucs_result.path)

if __name__ == "__main__":
    unittest.main()


