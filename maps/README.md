# Map test và map thực nghiệm — thành viên 4

`example_basic.json` chỉ là mẫu schema. Tạo các map riêng cho core, fragile, bridge/soft switch, heavy switch, split/merge và case kết hợp. Với mỗi map, ghi trong bảng dưới một chuỗi action ngắn và kết quả mong đợi; không cần tự chứng minh đường tối ưu bằng tay. Solver phải replay path qua `Board.transition` để xác nhận thắng.

| File | Cơ chế cần thử | Chuỗi action / trạng thái cần kiểm | Kết quả mong đợi |
|---|---|---|---|
| `example_basic.json` | Core | `RIGHT`, `RIGHT` từ start | Đứng trên goal và thắng |

Map TXT có thể là bản phác thảo; map dùng chạy chương trình phải chuyển sang JSON theo `docs/API.md` và được validate. Giữ tập benchmark cố định cho cả bốn solver.
