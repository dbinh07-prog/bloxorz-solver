# API dùng chung

Thành viên 1 chốt tên hàm và dữ liệu ở đây. Nếu cần đổi chỗ GUI, solver hoặc cơ chế nâng cao đang dùng, báo nhau trước khi sửa.

Tên file, hàm public và tham số đang theo repo mẫu. Contract bên dưới là phần nhóm cần tự triển khai; `mechanics.py` và `actions.py` là phần nhóm tách/thêm để làm việc song song. Các hàm trong bộ khung hiện chỉ báo `NotImplementedError`.

## Quy ước dữ liệu

- Tọa độ `(row, col)` là số nguyên, **0-based**; hàng tăng xuống dưới, cột tăng sang phải.
- `Orientation`: `STANDING`, `HORIZONTAL`, `VERTICAL`, `SPLIT`.
- Khối đứng: `pos1 == pos2`. Khối nằm ngang/dọc: `pos1` là ô trái/trên; `pos2` là ô phải/dưới. Split: `pos1` và `pos2` là hai cube phân biệt, `active_index` bằng `0` hoặc `1`.
- `bridge_states`: tuple sắp xếp theo ID, ví dụ `(("b1", False), ("b2", True))`. `True` nghĩa cầu mở, có thể đi qua.
- Action là chuỗi viết hoa từ `actions.py`: `UP`, `DOWN`, `LEFT`, `RIGHT`, `SWITCH`. Không dùng tên phím (`w`, `space`) trong engine/solver.

## Core

| API | Contract |
|---|---|
| `Block(row, col)` | Tạo khối đứng tại `(row, col)`. |
| `Block.copy()` | Trả khối độc lập, không mutate bản gốc. |
| `Block.get_cells()` | Trả `list[(row, col)]` các ô đang chiếm. Khối đứng: 1 ô; nằm/split: 2 ô. |
| `Block.state_key()` | Bao gồm orientation, vị trí và active_index khi split. |
| `Block.move(direction)` | Di chuyển theo action rồi trả `self` như repo tham chiếu; `Board.transition` phải làm việc trên bản copy. |
| `State(block, bridge_states, parent, action, cost)` | Node cho tìm kiếm. `parent/action/cost` là metadata, không phải identity. |
| `State.key()` | `(block.state_key(), bridge_states)`; dùng trong visited/best_cost. |
| `State.get_path()` | Lấy action từ root tới node hiện tại. |
| `Board(filename)` | Đọc/validate map JSON; xuất `start`, `goal`, `initial_bridge_states`. |
| `Board.normalize_bridge_states(states)` | Chuyển dict/tuple/None thành tuple ID đã sắp xếp. |
| `Board.bridge_state_dict(states)` | View dict để GUI vẽ cầu; không phải search key. |
| `Board.is_inside/is_bridge/is_fragile/get_switch/tile_type` | Query map cho renderer và luật; không mutate state. |
| `Board.is_floor/is_void(row, col, states)` | Xét cầu mở/đóng theo `states`; ngoài board là void. |
| `Board.available_actions(block)` | Trả list gồm 4 hướng; thêm `SWITCH` khi split. |
| `Board.transition(block, bridge_states, action)` | Trả `TransitionResult`, **không mutate input**. Action không biết thì `ValueError`; nước đi rơi thì `valid=False`. |
| `Board.is_win(block)` | Chỉ đúng khi khối đứng trên goal. |
| `Board.is_valid_block(block, bridge_states)` | Mọi ô khối chiếm phải có sàn; gọi `mechanics.is_special_supported` cho fragile. |
| `Board.get_action_cost(result, action)` | Cost dương, cùng quy tắc cho UCS/A*. Chỉ gọi với transition hợp lệ. |
| `Board.heuristic(block)` | Ước lượng cost còn lại; `h(goal)=0`, admissible theo `get_action_cost`. |

`TransitionResult` có `block`, `bridge_states`, `activated_switches`, `valid`. `valid=False` vẫn được trả để GUI có thể phát animation rơi; solver bỏ qua trạng thái đó. Không thay đổi board hoặc block đầu vào ngay cả khi không hợp lệ.

**Cost v0.1:** mỗi lần lăn tốn `1`; nếu landing trên ít nhất một ô fragile hợp lệ thì thêm `1`; mỗi switch vừa kích hoạt thêm `0.25`; action `SWITCH` khi split tốn `0.5` (không cộng chi phí lăn). Đây là cost không đồng đều theo repo tham chiếu, để UCS có ý nghĩa khác BFS. Thành viên 1 và 4 cùng đổi công thức nếu có lý do, và phải cập nhật test/heuristic/báo cáo đồng thời.

### Thứ tự xử lý transition

1. Chuẩn hóa bridge states và tạo bản sao `Block`.
2. Thực hiện basic roll hoặc `mechanics.move_split`/`SWITCH`.
3. Kiểm tra khối **hạ xuống được trên trạng thái cầu cũ**. Không cho khối kích hoạt công tắc khi đã rơi.
4. Gọi `mechanics.apply_special_tiles` để xử lý công tắc, split, bridge; chỉ kích hoạt khi vừa bắt đầu đè lên công tắc (tránh toggle lặp khi vẫn đứng yên trên đó).
5. Kiểm tra lại khối trên trạng thái cầu mới. Trả `TransitionResult`.

Thành viên 1 và 3 cùng kiểm tra trường hợp công tắc đóng cầu ngay dưới khối, split tới target không hợp lệ, và merge sau khi một cube đi tới ô kề. Nếu cần đổi thứ tự trên, chốt trước khi GUI/solver tích hợp.

## Advanced mechanics (`mechanics.py`)

| API | Contract |
|---|---|
| `move_split(block, action) -> Block` | Di chuyển cube active một ô hoặc đổi active khi `SWITCH`; không mutate input. |
| `is_special_supported(board, block) -> bool` | False khi đứng trên fragile; `Board.is_valid_block` gọi hàm này. |
| `split_block(block, targets) -> Block` | Tạo hai cube ở targets. |
| `merge_if_adjacent(block) -> Block` | Hai cube kề theo cạnh tự ghép thành khối nằm; các vị trí được chuẩn hóa. |
| `apply_special_tiles(board, old_block, moved_block, bridge_states)` | Trả `(block, bridge_states, activated_switches)` sau khi áp dụng fragile/bridge/switch/split. Không import GUI. |

Ô fragile cho khối nằm/split đi qua, nhưng không chịu được khối đứng. Soft switch: bất kỳ phần nào đè lên. Heavy/split switch: khối đầy đủ đứng trên ô. Hai cube tách không thắng và không kích hoạt heavy. Bridge `toggle` đảo trạng thái; `open`/`close` đặt cố định.

## Solver và GUI

| API | Contract |
|---|---|
| `get_successors(state, board)` | Duyệt `available_actions`, gọi `transition`, bỏ `valid=False`, tính cost bằng `get_action_cost`. |
| `bfs/ids/ucs/astar(board, start_block, start_bridge_states=None)` | Trả `SearchResult`. `ids` có thêm `max_depth=None`. |
| `solve(board, start_block, algorithm_name, start_bridge_states=None)` | Điều phối `BFS`, `IDS`, `UCS`, `ASTAR`/`A*`; tên không biết thì `ValueError`. |
| `SearchResult.path` | Danh sách action có thể replay từ trạng thái bắt đầu. |
| `SearchResult.steps` | `len(path)`. |
| `SearchResult.search_time` | Giây, không tính animation GUI. |
| `SearchResult.memory_usage` | Peak bytes khi tìm kiếm; `memory_usage_mb` là MiB. |
| `SearchResult.expanded_nodes` | Số node lấy ra để xét successor; phải cùng định nghĩa ở mọi solver. |
| `Game.try_move(action)` | Gọi `Board.transition`, cập nhật model/renderer sau animation. |
| `Game.play_next_solution_move()` | Replay từng action; mỗi bước vẫn gọi `try_move`. |

`found=False` thì path rỗng. Solver trả cả `solution_cost`, `generated_nodes`, `peak_frontier`. Với IDS, báo cáo nêu rõ số node mở rộng qua các vòng lặp có tính lặp lại. Chạy thực nghiệm cố định cùng map, cost, môi trường và số lần lặp.

## Map JSON

`maps/example_basic.json` là mẫu tối thiểu. `grid` là mảng chuỗi cùng chiều dài. `#` là void, `.` là floor, `F` fragile, `S` soft, `H` heavy, `X` split. `start`, `goal`, `position`, `targets` đều là `[row, col]`. Khối bắt đầu đứng ở `start`.

```json
{
  "grid": [".....", "..F..", "....."],
  "start": [1, 0],
  "goal": [1, 4],
  "bridges": {
    "b1": {"cells": [[2, 2]], "initial_open": false}
  },
  "switches": [
    {"id": "s1", "position": [0, 1], "type": "soft",
     "bridges": ["b1"], "action": "toggle"}
  ]
}
```

Ví dụ trên minh họa **schema**, không đảm bảo có lời giải. Cầu và công tắc định nghĩa trong metadata, không dựa riêng vào ký tự grid. `action` của switch nhận `toggle`, `open`, `close`; split switch thêm `targets` gồm đúng hai ô. Thành viên 4 sở hữu map thực nghiệm và mô tả kết quả mong đợi; thành viên 3 rà lại map có cơ chế nâng cao.

## Điểm còn phải chốt

- Heuristic: split switch **teleport** có thể đưa khối đến gần goal trong một bước. Manhattan/2 đơn thuần có thể overestimate; thành viên 1 phải chứng minh với cả teleport hoặc dùng cận dưới an toàn cho map có split (ví dụ `h=0` ban đầu, rồi cải tiến bằng relaxed graph có cạnh teleport). Kiểm tra nhất quán của `h` trên các transition thực tế.
- Nếu đổi cost v0.1, thành viên 1 + 4 cập nhật đồng thời UCS, A*, benchmark và phần giải thích trong báo cáo.
- Giới hạn của IDS trên map không có lời giải và cách báo timeout trong benchmark.
- Phương thức chọn cube bằng chuột (nếu có): GUI chuyển thành action/chỉ số hợp lệ theo cơ chế đã thống nhất; chuột không đi thẳng vào solver.
