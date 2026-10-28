from enum import Enum

from actions import ROLL_ACTIONS, SWITCH_ACTION


class Orientation(Enum):
    STANDING = 0
    HORIZONTAL = 1
    VERTICAL = 2
    SPLIT = 3


class Block:

    def __init__(self, row: int, col: int) -> None:
        self.pos1 = self.pos2 = self._cell((row, col))
        self.orientation = Orientation.STANDING
        self.active_index = 0

    def _cell(value) -> tuple[int, int]:
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise ValueError("A cell must contain [row, col]")
        if any(type(coordinate) is not int for coordinate in value):
            raise ValueError("Cell coordinates must be integers")
        return tuple(value)

    _cell = staticmethod(_cell)

    def split(cls, pos1: tuple[int, int], pos2: tuple[int, int], active_index: int = 0) -> "Block":
        first, second = cls._cell(pos1), cls._cell(pos2)
        if first == second:
            raise ValueError("Split cubes must occupy distinct cells")
        if type(active_index) is not int or active_index not in (0, 1):
            raise ValueError("active_index must be 0 or 1")
        block = cls(*first)
        block.pos2 = second
        block.orientation = Orientation.SPLIT
        block.active_index = active_index
        return block

    split = classmethod(split)

    def is_split(self) -> bool:
        return self.orientation == Orientation.SPLIT

    is_split = property(is_split)

    def copy(self) -> "Block":
        block = Block(*self.pos1)
        block.pos2 = self.pos2
        block.orientation = self.orientation
        block.active_index = self.active_index
        return block

    def get_cells(self) -> list[tuple[int, int]]:
        return [self.pos1] if self.orientation == Orientation.STANDING else [self.pos1, self.pos2]

    def get_active_cell(self) -> tuple[int, int]:
        if not self.is_split:
            raise ValueError("The block is not split")
        return (self.pos1, self.pos2)[self.active_index]

    def state_key(self) -> tuple:
        return (
            self.orientation.value,
            self.pos1,
            self.pos2,
            self.active_index if self.is_split else 0,
        )

    def move(self, direction: str) -> "Block":
        if not isinstance(direction, str):
            raise ValueError("Action must be a string")
        action = direction.upper()
        if action == SWITCH_ACTION:
            self.switch_active_cube()
        elif action in ROLL_ACTIONS:
            self._roll(action)
        else:
            raise ValueError(f"Unknown action: {direction}")
        return self

    def _split_action(self, action: str) -> None:

        from mechanics import move_split

        result = move_split(self.copy(), action)
        if not isinstance(result, Block):
            raise TypeError("mechanics.move_split must return Block")
        self.pos1, self.pos2 = result.pos1, result.pos2
        self.orientation, self.active_index = result.orientation, result.active_index

    def _roll(self, action: str) -> None:
        if self.is_split:
            self._split_action(action)
            return

        dr, dc = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}[action]
        row, col = self.pos1
        if self.orientation == Orientation.STANDING:
            self.pos1, self.pos2 = sorted(((row + dr, col + dc), (row + 2 * dr, col + 2 * dc)))
            self.orientation = Orientation.VERTICAL if dr else Orientation.HORIZONTAL
            return

        along_length = (
            self.orientation == Orientation.VERTICAL and dr != 0
            or self.orientation == Orientation.HORIZONTAL and dc != 0
        )
        if along_length:
            edge = max((self.pos1, self.pos2), key=lambda cell: cell[0] * dr + cell[1] * dc)
            self.pos1 = self.pos2 = (edge[0] + dr, edge[1] + dc)
            self.orientation = Orientation.STANDING
        else:
            self.pos1, self.pos2 = (
                (cell[0] + dr, cell[1] + dc) for cell in (self.pos1, self.pos2)
            )

    def move_up(self) -> None:
        self._roll("UP")

    def move_down(self) -> None:
        self._roll("DOWN")

    def move_left(self) -> None:
        self._roll("LEFT")

    def move_right(self) -> None:
        self._roll("RIGHT")

    def switch_active_cube(self) -> None:
        if not self.is_split:
            raise ValueError("Only a split block can switch its active cube")
        self._split_action(SWITCH_ACTION)

    def __str__(self) -> str:
        return f"{self.orientation.name}: {self.pos1}, {self.pos2}; active={self.active_index}"
