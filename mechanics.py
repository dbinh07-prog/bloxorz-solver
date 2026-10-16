"""Luật advanced thuần Python. Owner: thành viên 3.

Không import Ursina. Board gọi các hàm này; mọi solver được hưởng cùng luật.
"""

from typing import TYPE_CHECKING
from block import Block

if TYPE_CHECKING:
    from board import Board


def move_split(block: Block, action: str) -> Block:
    """Di chuyển cube đang active hoặc đổi active khi action == SWITCH."""
    raise NotImplementedError


def is_special_supported(board: "Board", block: Block) -> bool:
    """False nếu khối đứng trên fragile; các ô void/cầu do Board.is_floor xét."""
    raise NotImplementedError


def split_block(block: Block, targets: tuple[tuple[int, int], tuple[int, int]]) -> Block:
    """Tạo hai cube tại targets; không mutate block đầu vào."""
    raise NotImplementedError


def merge_if_adjacent(block: Block) -> Block:
    """Ghép hai cube đứng cạnh nhau thành khối nằm ngang/dọc."""
    raise NotImplementedError


def apply_special_tiles(
    board: "Board", old_block: Block, moved_block: Block, bridge_states: tuple
) -> tuple[Block, tuple[tuple[str, bool], ...], tuple[str, ...]]:
    """Kích hoạt soft/heavy/split switch và đổi cầu; trả block/states/IDs."""
    raise NotImplementedError
