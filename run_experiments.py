import csv
import re
from pathlib import Path

from algorithms.solver import solve
from block import Block
from board import Board

ALGORITHMS = ("BFS", "IDS", "UCS", "ASTAR")

def level_number(path: Path) -> int:
    match = re.search(r"\d+", path.stem)
    return int(match.group()) if match else 999


def run_level(level_path: Path, algorithm: str, repeats: int = 1) -> dict:
    lvl = level_number(level_path)
    record = {
        "level": lvl,
        "map_name": level_path.stem,
        "algorithm": algorithm,
        "found": False,
        "steps": 0,
        "cost": 0.0,
        "time_s": 0.0,
        "memory_mb": 0.0,
        "expanded_nodes": 0,
        "generated_nodes": 0,
        "peak_frontier": 0,
        "error": "",
    }

    times = []
    last_res = None

    for _ in range(max(1, repeats)):
        try:
            board = Board(level_path)
            start_block = Block(*board.start)
            res = solve(board, start_block, algorithm)
            last_res = res
            times.append(res.search_time)
        except Exception as e:
            record["error"] = f"{type(e).__name__}: {e}"
            return record

    if last_res is not None:
        record["found"] = last_res.found
        record["steps"] = last_res.steps
        record["cost"] = round(last_res.solution_cost, 2)
        record["time_s"] = round(sum(times) / len(times), 4)
        record["memory_mb"] = round(last_res.memory_usage_mb, 4)
        record["expanded_nodes"] = last_res.expanded_nodes
        record["generated_nodes"] = last_res.generated_nodes
        record["peak_frontier"] = last_res.peak_frontier

    return record


def main() -> None:
    root = Path(__file__).resolve().parent
    maps_dir = root / "maps"
    output_dir = root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    level_files = sorted(maps_dir.glob("level_*.json"), key=level_number)
    if not level_files:
        print("Không tìm thấy file map nào trong thư mục maps/!")
        return

    print("=" * 80)
    print(
        f"{'Level':<8} | {'Algo':<6} | {'Found':<6} | {'Steps':<6} | "
        f"{'Cost':<7} | {'Time (s)':<9} | {'Expanded':<9} | {'Memory (MB)'}"
    )
    print("-" * 80)

    all_records = []

    for level_path in level_files:
        for algo in ALGORITHMS:
            record = run_level(level_path, algo, repeats=1)
            all_records.append(record)

            status = "YES" if record["found"] else ("ERR" if record["error"] else "NO")
            print(
                f"{record['map_name']:<8} | {algo:<6} | {status:<6} | "
                f"{record['steps']:<6} | {record['cost']:<7} | {record['time_s']:<9} | "
                f"{record['expanded_nodes']:<9} | {record['memory_mb']}"
            )
        print("-" * 80)

    csv_file = output_dir / "benchmark_results.csv"
    fieldnames = [
        "level", "map_name", "algorithm", "found", "steps",
        "cost", "time_s", "memory_mb", "expanded_nodes",
        "generated_nodes", "peak_frontier", "error",
    ]

    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"Đã lưu toàn bộ kết quả thực nghiệm vào: {csv_file}")

if __name__ == "__main__":
    main()
