"""Search state dùng chung. Owner: thành viên 1."""

from block import Block


class State:
    block: Block
    bridge_states: tuple[tuple[str, bool], ...]
    parent: "State | None"
    action: str | None
    cost: float

    def __init__(
        self,
        block: Block,
        bridge_states: tuple = (),
        parent: "State | None" = None,
        action: str | None = None,
        cost: float = 0.0,
    ) -> None:
        raise NotImplementedError

    def copy(self) -> "State":
        raise NotImplementedError

    def key(self) -> tuple:
        """Chỉ block.state_key() + bridge_states; không gồm parent/action/cost."""
        raise NotImplementedError

    def get_path(self) -> list[str]:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError
