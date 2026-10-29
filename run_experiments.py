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
        "Level": lvl,
        "Map_Name": level_path.stem,
        "Algorithm": algorithm,
        "Found": False,
        "Steps": 0,
        "Cost": 0.0,
        "Time_s": 0.0,
        "Memory_MB": 0.0,
        "Expanded_Nodes": 0,
        "Generated_Nodes": 0,
        "Peak_Frontier": 0,
        "Path": "",
        "Error": "",
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
            record["Error"] = f"{type(e).__name__}: {e}"
            return record

    if last_res is not None:
        record["Found"] = last_res.found
        record["Steps"] = last_res.steps
        record["Cost"] = round(last_res.solution_cost, 2)
        record["Time_s"] = round(sum(times) / len(times), 4)
        record["Memory_MB"] = round(last_res.memory_usage_mb, 4)
        record["Expanded_Nodes"] = last_res.expanded_nodes
        record["Generated_Nodes"] = last_res.generated_nodes
        record["Peak_Frontier"] = last_res.peak_frontier
        record["Path"] = " ".join(last_res.path) if last_res.path else ""

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

            status = "YES" if record["Found"] else ("ERR" if record["Error"] else "NO")
            print(
                f"{record['Map_Name']:<8} | {algo:<6} | {status:<6} | "
                f"{record['Steps']:<6} | {record['Cost']:<7} | {record['Time_s']:<9} | "
                f"{record['Expanded_Nodes']:<9} | {record['Memory_MB']}"
            )
        print("-" * 80)

    csv_file = output_dir / "benchmark_results.csv"
    fieldnames = [
        "Level", "Map_Name", "Algorithm", "Found", "Steps",
        "Cost", "Time_s", "Memory_MB", "Expanded_Nodes",
        "Generated_Nodes", "Peak_Frontier", "Path", "Error",
    ]

    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"Saved benchmark results to: {csv_file}")

if __name__ == "__main__":
    main()
