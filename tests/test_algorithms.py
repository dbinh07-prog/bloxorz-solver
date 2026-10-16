"""Tên test tham khảo từ repo mẫu; thay các phần TODO bằng test của nhóm."""

import unittest


@unittest.skip("TODO: viết test cho phần này")
class SolverTests(unittest.TestCase):

    def replay(self, board, path):
        raise NotImplementedError

    def test_all_algorithms_solve_basic_and_advanced_levels(self):
        raise NotImplementedError

    def test_solver_can_change_the_active_split_cube(self):
        raise NotImplementedError

    def test_ucs_uses_non_uniform_cost(self):
        raise NotImplementedError
