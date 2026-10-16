"""Nạp map và điều phối duy nhất luật chuyển trạng thái. Owner: thành viên 1."""

from dataclasses import dataclass
from pathlib import Path

from block import Block


@dataclass(frozen=True)
class TransitionResult:
    block: Block
    bridge_states: tuple[tuple[str, bool], ...]
    activated_switches: tuple[str, ...]
    valid: bool


class Board:
    grid: list[list[str]]
    rows: int
    cols: int
    start: tuple[int, int]
    goal: tuple[int, int]
    bridge_at: dict[tuple[int, int], str]
    initial_bridge_states: tuple[tuple[str, bool], ...]

    def __init__(self, filename: str | Path) -> None:
        """Nạp và validate JSON theo docs/API.md."""
        raise NotImplementedError

    def normalize_bridge_states(self, bridge_states=None) -> tuple[tuple[str, bool], ...]:
        raise NotImplementedError

    def bridge_state_dict(self, bridge_states=None) -> dict[str, bool]:
        raise NotImplementedError

    def is_inside(self, row: int, col: int) -> bool:
        raise NotImplementedError

    def is_bridge(self, row: int, col: int) -> bool:
        raise NotImplementedError

    def is_fragile(self, row: int, col: int) -> bool:
        raise NotImplementedError

    def get_switch(self, row: int, col: int) -> dict | None:
        raise NotImplementedError

    def tile_type(self, row: int, col: int) -> str:
        raise NotImplementedError

    def is_floor(self, row: int, col: int, bridge_states=None) -> bool:
        raise NotImplementedError

    def is_void(self, row: int, col: int, bridge_states=None) -> bool:
        raise NotImplementedError

    def is_valid_block(self, block: Block, bridge_states=None) -> bool:
        raise NotImplementedError

    def is_goal(self, row: int, col: int) -> bool:
        raise NotImplementedError

    def is_win(self, block: Block) -> bool:
        raise NotImplementedError

    def available_actions(self, block: Block) -> list[str]:
        raise NotImplementedError

    def transition(self, block: Block, bridge_states, action: str) -> TransitionResult:
        """Không mutate input; basic roll -> kiểm tra landing -> mechanics -> kiểm tra lại."""
        raise NotImplementedError

    def get_action_cost(self, result: TransitionResult, action: str) -> float:
        """Một cost function dương, dùng chung cho UCS/A*."""
        raise NotImplementedError

    def heuristic(self, block: Block) -> float:
        """Lower bound cho cost còn lại; thành viên 1 chứng minh trong báo cáo."""
        raise NotImplementedError

    def estimated_state_count(self) -> int:
        """Cận trên thô cho IDS; không dùng làm số expanded thực tế."""
        raise NotImplementedError

    def print_board(self) -> None:
        raise NotImplementedError
