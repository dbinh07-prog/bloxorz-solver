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


    def test_solvers_on_unsolvable_maps(self):
        unsolvable_file_json = "maps/example_basic.json"
        board = Board(unsolvable_file_json)
        board.goal = (100, 100)

        for name in ("ASTAR","IDS","BFS","UCS"):
            with self.subTest(algorithm = name):
                result = solve(board, Block(*board.start),name, board.initial_bridge_states)
                self.assertFalse(result.found, f"Thuật toán {name} trả về False khi không có đường đi tới đích")
                self.assertEqual(result.path, [])
    
    def test_bfs_ids_StepCount(self):
        board = Board("maps/level_1.json")
        start_block = Block(*board.start)
        bfs_result = solve(board, start_block, "BFS", board.initial_bridge_states)
        ids_result = solve(board, start_block, "IDS", board.initial_bridge_states)

        self.assertTrue(bfs_result.found)
        self.assertTrue(ids_result.found)
        self.assertEqual(bfs_result.steps, ids_result.steps   , f"Thuật toán BFS sinh ra {bfs_result.steps} bước, thuật toán IDS sinh ra {ids_result.steps}, phải có số bước bằng nhau")




    def test_all_solvers_reject_invalid_start(self):
        board = Board("maps/example_basic.json")
        for name in ("BFS", "IDS", "UCS", "ASTAR"):
            with self.subTest(algorithm=name):
                result = solve(board, Block(-1, -1), name)
                self.assertFalse(result.found)
                self.assertEqual(result.expanded_nodes, 0)
                self.assertEqual(result.generated_nodes, 0)

    def test_start_at_goal_has_one_generated_state(self):
        board = Board("maps/example_basic.json")
        for name in ("BFS", "IDS", "UCS", "ASTAR"):
            with self.subTest(algorithm=name):
                result = solve(board, Block(*board.goal), name)
                self.assertTrue(result.found)
                self.assertEqual(result.path, [])
                self.assertEqual(result.generated_nodes, 1)
                self.assertEqual(result.expanded_nodes, 1)

if __name__ == "__main__":
    unittest.main()
