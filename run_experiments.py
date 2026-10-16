"""Benchmark cố định cho bốn solver. Owner: thành viên 4."""

from pathlib import Path


ALGORITHMS = ("BFS", "IDS", "UCS", "ASTAR")


def level_number(path: Path) -> int:
    raise NotImplementedError


def run_level(level_path: Path, algorithm: str, repeats: int) -> dict:
    raise NotImplementedError


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
