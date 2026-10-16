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

## Làm song song trước khi core xong

- **Thành viên 2:** dựng menu, màn chọn level, bàn 3D và thao tác chuột/phím trong `game/`, `scenes/`, `ui/`. Có thể dùng map/trạng thái giả để kiểm tra giao diện; lúc ghép thật chỉ gọi `Board.transition` theo `docs/API.md`.
- **Thành viên 3:** làm luật fragile, switch, cầu và tách/đổi/ghép ở `mechanics.py` theo dữ liệu trong `docs/API.md`. Khi core chưa chạy, có thể tự tạo đối tượng giả có các thuộc tính/phương thức cần dùng để thử từng hàm; sau đó kiểm tra lại với `Block`/`Board` thật. Nếu cần thêm dữ liệu, nhắn thành viên 1 để chốt.
- **Thành viên 4:** viết map JSON và kết quả mong đợi trước; ưu tiên `algorithms/search_result.py`, `algorithms/metrics.py`, `algorithms/successor.py`, rồi làm BFS/IDS/UCS và `algorithms/solver.py`. Các file dùng chung này cũng phục vụ A*. Nếu dùng board giả để test, nó phải có đúng các hàm mà `get_successors` gọi: `available_actions`, `transition`, `get_action_cost`; board không trực tiếp trả successor. Test với core thật và benchmark làm sau.
- **Thành viên 5:** soạn checklist trong `docs/QA.md`, khung báo cáo và kịch bản demo. Chơi thử, ghi lỗi thật khi bản game đã nối xong.

Như vậy mỗi người có việc riêng để làm ngay. Phần ghép GUI, mechanics và solver với core sẽ chờ `Block`, `State`, `Board.transition` hoạt động; đừng sửa chéo các file đó khi chưa thống nhất với thành viên 1.

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

`assets/` hiện chỉ có các file `.gitkeep` để giữ thư mục; thành viên 2 thêm tài nguyên sau. Với `maps/example_basic.json`, kết quả mong đợi theo luật lăn là đi `RIGHT`, `RIGHT` từ start sẽ đứng trên goal; cần chạy test lại khi core hoàn thành. `output/` chỉ giữ `.gitkeep`; file chạy thử trong đó được `.gitignore` bỏ qua. Số liệu/ảnh nào dùng trong báo cáo thì chép vào `report/`. Map JSON, mã nguồn, test, báo cáo và asset hình/âm thanh không bị các quy tắc ignore hiện tại loại bỏ, nhưng vẫn cần `git add` và commit để đưa lên repo. File video demo bị ignore; đặt link video trong báo cáo.

## Cách nối các phần

- Tên action chung là `UP`, `DOWN`, `LEFT`, `RIGHT`, `SWITCH` trong `actions.py`.
- Cả chơi tay lẫn solver đều gọi `Board.transition`. GUI chỉ gửi action và vẽ kết quả, không tự tính luật chơi.
- Thành viên 3 viết luật nâng cao trong `mechanics.py`; thành viên 1 nối nó vào `Board.transition`.
- Khi người chơi đổi cube, thành viên 2 chuyển input thành `SWITCH`, thành viên 3 viết cách đổi cube active, thành viên 1 nối lời gọi qua `Block`/`Board`. GUI không tự sửa `active_index`.
- Thành viên 4 dùng `Board.get_action_cost` cho UCS; A* dùng cùng cost đó. Tất cả solver trả `SearchResult` để GUI phát lại.
- Chi tiết tên hàm, tham số, kiểu kết quả và format map nằm ở [docs/API.md](docs/API.md). Muốn đổi API chung thì báo các phần đang dùng nó trước khi sửa.

## Chạy sau khi đã code xong

Mở terminal tại thư mục gốc của dự án, cùng chỗ với `main.py` và `requirements.txt`:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python main.py
python run_experiments.py
```

Nhóm dùng Python 3.12 để thống nhất môi trường. Bản Ursina 8.3.0 hiện yêu cầu Python từ 3.12 theo [metadata trên PyPI](https://pypi.org/project/ursina/8.3.0/). `requirements.txt` hiện chưa khóa phiên bản Ursina; thành viên 2 chốt phiên bản dùng chung sau khi chạy thử GUI.

Hiện game và benchmark mới có khung hàm nên chưa chạy được. Lệnh test chỉ phát hiện 12 test đang skip, chưa kiểm tra luật chơi; khi tự viết nội dung test, bỏ decorator `@unittest.skip(...)` ở lớp test tương ứng. `tests/test_gui.py` và `test_ursina.py` vẫn là chỗ trống để thành viên 2 bổ sung.

## Tham khảo repo mẫu

Bộ khung đã đối chiếu tên file Python, tên class, hàm public và tên tham số với [repo mẫu tại commit `4f3afeb`](https://github.com/TranTai35/bloxorz-game/tree/4f3afebd0eec1787546fdcb8b8bab227d44e4d4e). Đây là mốc để mọi người tra cùng một bản. Phần xử lý, kế thừa class Ursina và giá trị màu/bố cục do nhóm tự viết; các default phụ thuộc giao diện hiện để `None`. Chữ ký hàm giúp đối chiếu với repo mẫu, còn hành vi cần thực hiện theo `docs/API.md`.

Nhóm thêm `actions.py`, `mechanics.py`, `docs/` và `report/` để chia việc rõ hơn. Riêng luật switch/split được giao cho thành viên 3 trong `mechanics.py` rồi nối qua `Board.transition`; khi xem repo mẫu, đối chiếu phần đó với `board.py` và `block.py` của họ. Tên hàm dùng chung và định dạng map ghi ở [docs/API.md](docs/API.md).
