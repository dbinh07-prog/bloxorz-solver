"""Tên test tham khảo từ repo mẫu; thay các phần TODO bằng test của nhóm."""

import unittest


@unittest.skip("TODO: viết test cho phần này")
class TemporaryBoardTestCase(unittest.TestCase):

    def make_board(self, data):
        raise NotImplementedError

@unittest.skip("TODO: viết test cho phần này")
class BoardAdvancedTileTests(unittest.TestCase):

    def test_half_outside_board_is_invalid_without_index_error(self):
        raise NotImplementedError

    def test_fragile_tile_rejects_standing_but_supports_lying(self):
        raise NotImplementedError

    def test_soft_switch_opens_bridge_when_any_part_presses_it(self):
        raise NotImplementedError

    def test_heavy_switch_requires_standing(self):
        raise NotImplementedError

    def test_split_switch_teleports_and_cubes_rejoin(self):
        raise NotImplementedError
