"""Dữ liệu khối và chuyển động cơ bản. Owner: thành viên 1."""

from enum import Enum


class Orientation(Enum):
    STANDING = 0
    HORIZONTAL = 1
    VERTICAL = 2
    SPLIT = 3


class Block:
    """pos1/pos2 là (row, col); active_index là 0 hoặc 1 khi SPLIT.

    STANDING: pos1 == pos2. HORIZONTAL/VERTICAL: pos1 đứng trước pos2
    theo cột/hàng. SPLIT: hai vị trí là hai cube phân biệt.
    """

    pos1: tuple[int, int]
    pos2: tuple[int, int]
    orientation: Orientation
    active_index: int

    def __init__(self, row: int, col: int) -> None:
        raise NotImplementedError

    @classmethod
    def split(cls, pos1: tuple[int, int], pos2: tuple[int, int], active_index: int = 0) -> "Block":
        """Adapter cho mechanics.split_block; không đặt luật tách trong GUI."""
        raise NotImplementedError

    @property
    def is_split(self) -> bool:
        raise NotImplementedError

    def copy(self) -> "Block":
        raise NotImplementedError

    def get_cells(self) -> list[tuple[int, int]]:
        raise NotImplementedError

    def get_active_cell(self) -> tuple[int, int]:
        raise NotImplementedError

    def state_key(self) -> tuple:
        """Bao gồm orientation, hai vị trí và active_index khi SPLIT."""
        raise NotImplementedError

    def move(self, direction: str) -> "Block":
        """Mutate rồi trả self; SWITCH/SPLIT gọi logic trong mechanics.py."""
        raise NotImplementedError

    def move_up(self) -> None:
        raise NotImplementedError

    def move_down(self) -> None:
        raise NotImplementedError

    def move_left(self) -> None:
        raise NotImplementedError

    def move_right(self) -> None:
        raise NotImplementedError

    def switch_active_cube(self) -> None:
        """Adapter cho mechanics.move_split khi action là SWITCH."""
        raise NotImplementedError
