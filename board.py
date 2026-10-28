import json
from collections import deque
from collections.abc import Mapping
from pathlib import Path

from actions import ALL_ACTIONS, ROLL_ACTIONS, SWITCH_ACTION
from block import Block, Orientation


class TransitionResult:

    def __init__(
        self,
        block: Block,
        bridge_states: tuple[tuple[str, bool], ...],
        activated_switches: tuple[str, ...],
        valid: bool,
    ) -> None:
        self.block = block
        self.bridge_states = bridge_states
        self.activated_switches = activated_switches
        self.valid = valid


class Board:
    SPECIAL_GRID_TILES = {"F": "fragile", "S": "soft", "H": "heavy", "X": "split"}

    def __init__(self, filename: str | Path) -> None:
        with Path(filename).open(encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict):
            raise ValueError("Level JSON must be an object")
        grid = data.get("grid")
        if not isinstance(grid, list) or not grid or any(not isinstance(row, str) or not row for row in grid):
            raise ValueError("grid must be a nonempty list of nonempty strings")
        if len({len(row) for row in grid}) != 1:
            raise ValueError("All grid rows must have the same length")
        self.grid = [list(row) for row in grid]
        self.rows, self.cols = len(grid), len(grid[0])
        self.start = self._map_cell(data.get("start"), "start")
        self.goal = self._map_cell(data.get("goal"), "goal")
        self.bridges = self._parse_bridges(data.get("bridges", {}))
        self.bridge_at = {}
        for bridge_id, config in self.bridges.items():
            for cell in config["cells"]:
                if cell in self.bridge_at:
                    raise ValueError(f"Multiple bridges occupy {cell}")
                self.bridge_at[cell] = bridge_id
        self.switches = self._parse_switches(data.get("switches", []))
        self.switch_at = {switch["position"]: switch for switch in self.switches}
        self.fragile_cells = {
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.grid[row][col] == "F"
        }
        fragile = data.get("fragile", [])
        if not isinstance(fragile, list):
            raise ValueError("fragile must be a list of cells")
        self.fragile_cells.update(self._map_cell(cell, "fragile cell") for cell in fragile)
        self.initial_bridge_states = tuple(sorted(
            (bridge_id, config["initial_open"]) for bridge_id, config in self.bridges.items()
        ))
        self._heuristic_tables = {}
        if not self.is_floor(*self.start, self.initial_bridge_states) or self.is_fragile(*self.start):
            raise ValueError("The start must support a standing block initially")

    def _map_cell(self, value, label: str) -> tuple[int, int]:
        try:
            cell = Block._cell(value)
        except ValueError as error:
            raise ValueError(f"Invalid {label}: {value!r}") from error
        if not self.is_inside(*cell):
            raise ValueError(f"{label} lies outside the grid: {cell}")
        return cell

    def _identifier(value, label: str) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} must be a nonempty string")
        return value

    _identifier = staticmethod(_identifier)

    def _parse_bridges(self, raw) -> dict:
        if isinstance(raw, dict):
            entries = []
            for bridge_id, config in raw.items():
                if not isinstance(config, dict):
                    raise ValueError("Each bridge must be an object")
                entries.append({**config, "id": bridge_id})
        elif isinstance(raw, list):
            entries = raw
        else:
            raise ValueError("bridges must be an object or a list")
        result = {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError("Each bridge must be an object")
            bridge_id = self._identifier(entry.get("id", f"bridge_{index + 1}"), "Bridge ID")
            cells = entry.get("cells")
            if not isinstance(cells, list) or not cells:
                raise ValueError(f"Bridge {bridge_id} needs a nonempty cells list")
            cells = tuple(self._map_cell(cell, f"Bridge {bridge_id} cell") for cell in cells)
            if len(set(cells)) != len(cells):
                raise ValueError(f"Bridge {bridge_id} repeats a cell")
            opened = entry.get("initial_open", entry.get("open", False))
            if type(opened) is not bool or bridge_id in result:
                raise ValueError(f"Invalid or duplicate bridge {bridge_id}")
            result[bridge_id] = {"cells": cells, "initial_open": opened}
        return result

    def _parse_switches(self, raw) -> list[dict]:
        if not isinstance(raw, list):
            raise ValueError("switches must be a list")
        result, identifiers, positions = [], set(), set()
        for index, entry in enumerate(raw):
            if not isinstance(entry, dict):
                raise ValueError("Each switch must be an object")
            switch_id = self._identifier(entry.get("id", f"switch_{index + 1}"), "Switch ID")
            position = self._map_cell(entry.get("position"), f"Switch {switch_id} position")
            kind = entry.get("type", "soft")
            kind = kind.lower() if isinstance(kind, str) else None
            if kind not in {"soft", "heavy", "split"}:
                raise ValueError(f"Unknown switch type: {kind}")
            action = entry.get("action", "toggle")
            if entry.get("behavior") == "permanent":
                target_state = entry.get("state", "open")
                if target_state not in {"open", "close", "closed"}:
                    raise ValueError("Permanent switch state must be open or closed")
                action = "open" if target_state == "open" else "close"
            action = action.lower() if isinstance(action, str) else None
            if action not in {"toggle", "open", "close"}:
                raise ValueError(f"Unknown switch action: {action}")
            bridge_ids = entry.get("bridges", [])
            if not isinstance(bridge_ids, list) or any(not isinstance(item, str) for item in bridge_ids):
                raise ValueError("Switch bridges must be a list of string IDs")
            if any(bridge_id not in self.bridges for bridge_id in bridge_ids):
                raise ValueError(f"Switch {switch_id} refers to an unknown bridge")
            if len(set(bridge_ids)) != len(bridge_ids):
                raise ValueError(f"Switch {switch_id} repeats a bridge ID")
            targets = entry.get("targets")
            if targets is not None:
                if not isinstance(targets, list) or len(targets) != 2:
                    raise ValueError("Split targets must contain exactly two cells")
                targets = tuple(self._map_cell(cell, "Split target") for cell in targets)
                if targets[0] == targets[1]:
                    raise ValueError("Split targets must be distinct")
            if kind == "split" and targets is None:
                raise ValueError(f"Split switch {switch_id} needs targets")
            if switch_id in identifiers or position in positions:
                raise ValueError("Switch IDs and positions must be unique")
            identifiers.add(switch_id)
            positions.add(position)
            result.append({
                "id": switch_id, "position": position, "type": kind,
                "bridges": tuple(bridge_ids), "action": action, "targets": targets,
            })
        return result

    def normalize_bridge_states(self, bridge_states=None) -> tuple[tuple[str, bool], ...]:
        if bridge_states is None:
            return self.initial_bridge_states
        items = bridge_states.items() if isinstance(bridge_states, Mapping) else bridge_states
        try:
            states = dict(items)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid bridge states") from error
        if any(key not in self.bridges or type(value) is not bool for key, value in states.items()):
            raise ValueError("Bridge states must use known IDs and boolean values")
        return tuple(sorted(
            (bridge_id, states.get(bridge_id, config["initial_open"]))
            for bridge_id, config in self.bridges.items()
        ))

    def bridge_state_dict(self, bridge_states=None) -> dict[str, bool]:
        return dict(self.normalize_bridge_states(bridge_states))

    def is_inside(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_bridge(self, row: int, col: int) -> bool:
        return (row, col) in self.bridge_at

    def is_fragile(self, row: int, col: int) -> bool:
        return (row, col) in self.fragile_cells

    def get_switch(self, row: int, col: int) -> dict | None:
        return self.switch_at.get((row, col))

    def tile_type(self, row: int, col: int) -> str:
        cell = row, col
        if not self.is_inside(row, col):
            return "void"
        if self.is_goal(row, col):
            return "goal"
        if cell in self.bridge_at:
            return "bridge"
        if cell in self.switch_at:
            return self.switch_at[cell]["type"]
        if cell in self.fragile_cells:
            return "fragile"
        if cell == self.start:
            return "floor"
        return self.SPECIAL_GRID_TILES.get(self.grid[row][col], "void" if self.grid[row][col] == "#" else "floor")

    def is_floor(self, row: int, col: int, bridge_states=None) -> bool:
        if not self.is_inside(row, col):
            return False
        cell = row, col
        if cell in self.bridge_at:
            return self.bridge_state_dict(bridge_states)[self.bridge_at[cell]]
        return (
            cell in self.switch_at or cell in self.fragile_cells
            or cell in (self.start, self.goal) or self.grid[row][col] != "#"
        )

    def is_void(self, row: int, col: int, bridge_states=None) -> bool:
        return not self.is_floor(row, col, bridge_states)

    def is_valid_block(self, block: Block, bridge_states=None) -> bool:
        states = self.normalize_bridge_states(bridge_states)
        if not all(self.is_floor(*cell, states) for cell in block.get_cells()):
            return False
        if any(self.is_fragile(*cell) for cell in block.get_cells()):
            from mechanics import is_special_supported

            return is_special_supported(self, block.copy())
        return True

    def is_goal(self, row: int, col: int) -> bool:
        return (row, col) == self.goal

    def is_win(self, block: Block) -> bool:
        return block.orientation == Orientation.STANDING and block.pos1 == self.goal

    def available_actions(self, block: Block) -> list[str]:
        return list(ROLL_ACTIONS) + ([SWITCH_ACTION] if block.is_split else [])

    def transition(self, block: Block, bridge_states, action: str) -> TransitionResult:
        if not isinstance(action, str) or action.upper() not in ALL_ACTIONS:
            raise ValueError(f"Unknown action: {action}")
        action = action.upper()
        states = self.normalize_bridge_states(bridge_states)
        moved = block.copy().move(action)
        if not self.is_valid_block(moved, states):
            return TransitionResult(moved, states, (), False)
        activated = ()
        if self.switches or moved.is_split:
            from mechanics import apply_special_tiles

            moved, new_states, activated = apply_special_tiles(self, block.copy(), moved, states)
            if not isinstance(moved, Block):
                raise TypeError("mechanics.apply_special_tiles must return a Block")
            states = self.normalize_bridge_states(new_states)
        return TransitionResult(moved, states, tuple(activated), self.is_valid_block(moved, states))

    def get_action_cost(self, result: TransitionResult, action: str) -> float:
        if not result.valid:
            raise ValueError("Cannot assign search cost to an invalid transition")
        if not isinstance(action, str) or action.upper() not in ALL_ACTIONS:
            raise ValueError(f"Unknown action: {action}")
        if action.upper() == SWITCH_ACTION:
            return 0.5
        fragile_penalty = 1.0 if any(self.is_fragile(*cell) for cell in result.block.get_cells()) else 0.0
        return 1.0 + fragile_penalty + 0.25 * len(result.activated_switches)

    def _pattern_key(self, block: Block) -> tuple:
        shape = block.orientation.value
        first, second = block.pos1, block.pos2
        if shape == Orientation.SPLIT.value:
            first, second = sorted((first, second))
        return shape, first, second

    def _pattern_floor(self) -> set:
        opened = {bridge_id: True for bridge_id in self.bridges}
        return {
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.is_floor(row, col, opened)
        }

    def _build_pattern_distances(self, include_split):
        floor = self._pattern_floor()
        self._heuristic_uses_pairs = include_split and len(floor) * (len(floor) - 1) // 2 <= 10_000
        if self.goal not in floor or self.goal in self.fragile_cells:
            return {}
        paired = self._heuristic_uses_pairs
        self._heuristic_cells = {cell: index for index, cell in enumerate(sorted(floor))} if paired else {}
        cell_ids = self._heuristic_cells
        neighbors = {}
        if paired:
            for (row, col), index in cell_ids.items():
                neighbors[index] = [
                    cell_ids[cell] for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if (cell := (row + dr, col + dc)) in cell_ids
                ]
        portals = {}
        if include_split:
            for switch in self.switches:
                if switch["type"] == "split" and all(cell in floor for cell in switch["targets"]):
                    targets = switch["targets"]
                    keys = (tuple(sorted(cell_ids[cell] for cell in targets)),) if paired else targets
                    for target in keys:
                        portals.setdefault(target, []).append(switch["position"])

        goal_pose = (0, self.goal, self.goal)
        distance = {goal_pose: 0}
        unreachable = float("inf")
        pending = deque([(goal_pose, 0)])
        while pending:
            pose, queued_cost = pending.popleft()
            if distance[pose] != queued_cost:
                continue
            shape, first, second = pose
            earlier_poses = []
            if shape == 3:
                if paired:
                    for entry in portals.get((first, second), ()):
                        if entry not in self.fragile_cells:
                            earlier_poses.append(((0, entry, entry), 0))
                    if second not in neighbors[first]:
                        for stationary, moving in ((first, second), (second, first)):
                            for cell in neighbors[moving]:
                                a, b = (stationary, cell) if stationary < cell else (cell, stationary)
                                earlier_poses.append(((3, a, b), 1))
                else:
                    row, col = first
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        cell = row + dr, col + dc
                        if cell in floor:
                            earlier_poses.append(((3, cell, cell), 1))
                    for entry in portals.get(first, ()):
                        if entry not in self.fragile_cells:
                            earlier_poses.append(((0, entry, entry), 0))
            else:
                row, col = first
                if shape == 0:
                    rolls = (
                        (2, (row - 2, col), (row - 1, col)),
                        (2, (row + 1, col), (row + 2, col)),
                        (1, (row, col - 2), (row, col - 1)),
                        (1, (row, col + 1), (row, col + 2)),
                    )
                elif shape == 1:
                    rolls = (
                        (1, (row - 1, col), (row - 1, col + 1)),
                        (1, (row + 1, col), (row + 1, col + 1)),
                        (0, (row, col - 1), (row, col - 1)),
                        (0, (row, col + 2), (row, col + 2)),
                    )
                else:
                    rolls = (
                        (0, (row - 1, col), (row - 1, col)),
                        (0, (row + 2, col), (row + 2, col)),
                        (2, (row, col - 1), (row + 1, col - 1)),
                        (2, (row, col + 1), (row + 1, col + 1)),
                    )
                for old_shape, old_first, old_second in rolls:
                    if old_first in floor and old_second in floor:
                        if old_shape != 0 or old_first not in self.fragile_cells:
                            earlier_poses.append(((old_shape, old_first, old_second), 1))
                if include_split and shape != 0:
                    if paired:
                        first_id, second_id = cell_ids[first], cell_ids[second]
                        earlier_poses.append(((3, first_id, second_id), 0))
                        for stationary, moving in ((first_id, second_id), (second_id, first_id)):
                            for cell in neighbors[moving]:
                                a, b = (stationary, cell) if stationary < cell else (cell, stationary)
                                earlier_poses.append(((3, a, b), 1))
                    else:
                        earlier_poses.extend((((3, first, first), 0), ((3, second, second), 0)))

            for earlier, edge_cost in earlier_poses:
                lower_cost = queued_cost + edge_cost
                if lower_cost >= distance.get(earlier, unreachable):
                    continue
                distance[earlier] = lower_cost
                if len(distance) > 100_000:
                    return None
                entry = earlier, lower_cost
                if edge_cost == 0:
                    pending.appendleft(entry)
                else:
                    pending.append(entry)
        return distance

    def heuristic(self, block: Block) -> float:
        if self.rows * self.cols <= 64 and not self.switches:
            row, col = self.goal
            nearest = min(abs(cell[0] - row) + abs(cell[1] - col) for cell in (block.pos1, block.pos2))
            return float(max((nearest + 1) // 2, int(block.orientation != Orientation.STANDING)))
        if not self._heuristic_tables:
            include_split = block.is_split or any(switch["type"] == "split" for switch in self.switches)
            self._heuristic_tables[include_split] = self._build_pattern_distances(include_split)
        elif block.is_split and True not in self._heuristic_tables:
            self._heuristic_tables[True] = self._build_pattern_distances(True)
        distances = self._heuristic_tables.get(True, self._heuristic_tables.get(False))
        if distances is None:
            return 0.0
        if not distances:
            return float("inf")
        if block.is_split and not self._heuristic_uses_pairs:
            return float(max(
                distances.get((3, block.pos1, block.pos1), float("inf")),
                distances.get((3, block.pos2, block.pos2), float("inf")),
            ))
        if block.is_split:
            first, second = sorted((self._heuristic_cells[block.pos1], self._heuristic_cells[block.pos2]))
            return float(distances.get((3, first, second), float("inf")))
        return float(distances.get(self._pattern_key(block), float("inf")))

    def estimated_state_count(self) -> int:
        cells = self.rows * self.cols

        return (3 * cells + 2 * cells * cells) * (1 << len(self.bridges))

    def print_board(self) -> None:
        for row in self.grid:
            print(" ".join(row))
