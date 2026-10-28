from collections.abc import Mapping
from math import isfinite

from block import Block


class State:
    def __init__(
        self,
        block: Block,
        bridge_states: tuple = (),
        parent: "State | None" = None,
        action: str | None = None,
        cost: float = 0.0,
    ) -> None:
        bridge_entries = bridge_states.items() if isinstance(bridge_states, Mapping) else bridge_states
        bridge_config = dict(bridge_entries)
        if any(not isinstance(key, str) or type(value) is not bool for key, value in bridge_config.items()):
            raise ValueError("Bridge states must map string IDs to booleans")
        if not isinstance(cost, (int, float)) or not isfinite(cost) or cost < 0:
            raise ValueError("State cost must be finite and nonnegative")
        self.block = block.copy()
        self.bridge_states = tuple(sorted(bridge_config.items()))
        self.parent = parent
        self.action = action
        self.cost = float(cost)

    def copy(self) -> "State":
        return State(self.block, self.bridge_states, self.parent, self.action, self.cost)

    def key(self) -> tuple:
        return self.block.state_key(), self.bridge_states

    def get_path(self) -> list[str]:
        reverse_route = []
        cursor = self
        while cursor.parent is not None:
            if cursor.action is None:
                raise ValueError("A non-root state must have an incoming action")
            reverse_route.append(cursor.action)
            cursor = cursor.parent
        return list(reversed(reverse_route))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return NotImplemented
        return self.key() == other.key()

    def __hash__(self) -> int:
        return hash(self.key())

    def __str__(self) -> str:
        return (
            f"State(block={self.block}, bridges={dict(self.bridge_states)}, "
            f"cost={self.cost:.2f})"
        )
