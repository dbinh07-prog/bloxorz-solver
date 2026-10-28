# Bloxorz Solver

## Chia việc

| Thành viên | File/folder làm chính | Việc cần làm |
|---|---|---|
| **1 — Core + A\*** | `actions.py`, `block.py`, `state.py`, `board.py`, `algorithms/astar.py`, `tests/test_block.py`, `docs/API.md` | Chốt tên hàm và dữ liệu chung; làm luật lăn khối, kiểm tra nước đi/thắng, A* và heuristic. |
| **2 — GUI 3D** | `main.py`, `app_controller.py`, `game/`, `scenes/`, `ui/`, `assets/`, `test_ursina.py`, `tests/test_gui.py` | Giao diện, input chuột/phím, vẽ map và khối, animation, phát lại lời giải. Nhận thao tác đổi cube rồi gửi action cho core. |
| **3 — Cơ chế nâng cao** | `mechanics.py`, `tests/test_board_advanced.py` | Fragile, cầu, ba loại switch, tách/đổi/ghép khối. Nếu cần thêm dữ liệu vào `Block` hay `Board`, trao đổi với thành viên 1. |
| **4 — Solver + map** | `algorithms/bfs.py`, `algorithms/ids.py`, `algorithms/ucs.py`, `algorithms/successor.py`, `algorithms/solver.py`, `algorithms/search_result.py`, `algorithms/metrics.py`, `maps/`, `run_experiments.py`, `tests/test_algorithms.py` | BFS/IDS/UCS, map JSON, benchmark và số liệu so sánh cả bốn solver. TXT dùng để phác thảo map; map chạy chương trình phải là JSON. Kết quả benchmark để trong `output/`. |
| **5 — Test thủ công + tài liệu** | `docs/QA.md`, `report/`, phần hướng dẫn sử dụng trong `README.md` | Chơi thử theo map của thành viên 4, ghi lỗi và bước tái hiện; gom phần báo cáo của cả nhóm, hoàn thiện video demo. |

Ai viết phần nào thì tự viết test cho phần đó. Báo cáo cần nội dung chuyên môn từ cả năm người; thành viên 5 tổng hợp và chỉnh bản cuối.

## Bản hiện tại

Đã ghép core và A* với cơ chế nâng cao, BFS/IDS/UCS, 12 level và giao diện 3D của nhóm. Map `example_basic.json` là màn thử hai nước `RIGHT`, `RIGHT`.

Chơi tay và phát lại lời giải đều gọi `Board.transition`. Solver chạy trong tiến trình riêng để giao diện vẫn nhận thao tác; quay lại menu hoặc khởi động lại sẽ hủy lần tìm kiếm hiện tại.

## Các folder dùng để làm gì?

```text
block.py, state.py, board.py   luật chơi và trạng thái
mechanics.py                  cơ chế nâng cao
algorithms/                   bốn solver, kết quả và cách đo số liệu
game/                         gameplay, vẽ bàn/khối, camera, âm thanh
scenes/, ui/                  menu, chọn màn, chọn thuật toán, giao diện
assets/                       fonts/, sounds/, sprites/, texture/
maps/                         level JSON và map test của thành viên 4
tests/                        test tự động theo từng phần
docs/                         API dùng chung và checklist test thủ công
output/                       file tạm sinh ra khi chạy benchmark, không commit
report/                       báo cáo, bảng số liệu và hình đã chọn để nộp
```

`assets/` chứa font, hình và âm thanh của giao diện. `output/` chỉ giữ `.gitkeep` trong Git; kết quả benchmark được tạo khi chạy. Số liệu hoặc ảnh dùng cho báo cáo thì chép vào `report/`. Video demo để ngoài repo và ghi link trong báo cáo.

## Cách nối các phần

- Tên action chung là `UP`, `DOWN`, `LEFT`, `RIGHT`, `SWITCH` trong `actions.py`.
- Cả chơi tay lẫn solver đều gọi `Board.transition`. GUI chỉ gửi action và vẽ kết quả, không tự tính luật chơi.
- Thành viên 3 viết luật nâng cao trong `mechanics.py`; thành viên 1 nối nó vào `Board.transition`.
- Khi người chơi đổi cube, thành viên 2 chuyển input thành `SWITCH`, thành viên 3 viết cách đổi cube active, thành viên 1 nối lời gọi qua `Block`/`Board`. GUI không tự sửa `active_index`.
- Thành viên 4 dùng `Board.get_action_cost` cho UCS; A* dùng cùng cost đó. Tất cả solver trả `SearchResult` để GUI phát lại.
- Chi tiết tên hàm, tham số, kiểu kết quả và format map nằm ở [docs/API.md](docs/API.md). Muốn đổi API chung thì báo các phần đang dùng nó trước khi sửa.

## Cài và chạy

Dùng Python 3.12, mở terminal tại thư mục dự án:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Nếu đã có `.venv` thì chỉ cần chạy lệnh cuối. Nhóm dùng Ursina 8.3.0 theo `requirements.txt`.

- **PLAY:** chọn màn rồi dùng WASD hoặc phím mũi tên để lăn.
- **SPACE/TAB:** đổi cube đang điều khiển khi khối đã tách.
- **R:** chơi lại; **ESC:** quay lại chọn màn.
- **AI SOLVER:** chọn màn, chọn BFS/IDS/UCS/A*, chờ tìm kiếm rồi xem phát lại.

Chạy test và xuất bảng so sánh:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe run_experiments.py
```

Benchmark lưu ở `output/benchmark_results.csv`. BFS/IDS tìm ít hành động nhất; UCS/A* tối thiểu tổng chi phí theo luật chung. Một số test core trong khung cũ vẫn đang skip; test nâng cao, solver và GUI đã có nội dung chạy thật.

## Tham khảo repo mẫu

Bộ khung đã đối chiếu tên file Python, tên class, hàm public và tên tham số với [repo mẫu tại commit `4f3afeb`](https://github.com/TranTai35/bloxorz-game/tree/4f3afebd0eec1787546fdcb8b8bab227d44e4d4e). Đây là mốc để mọi người tra cùng một bản. Phần xử lý và giao diện do nhóm tự viết. Chữ ký hàm giúp đối chiếu với repo mẫu, còn hành vi cần thực hiện theo `docs/API.md`.

Nhóm thêm `actions.py`, `mechanics.py`, `docs/` và `report/` để chia việc rõ hơn. Riêng luật switch/split được giao cho thành viên 3 trong `mechanics.py` rồi nối qua `Board.transition`; khi xem repo mẫu, đối chiếu phần đó với `board.py` và `block.py` của họ. Tên hàm dùng chung và định dạng map ghi ở [docs/API.md](docs/API.md).
