# Map test và map thực nghiệm — thành viên 4

`example_basic.json` chỉ là mẫu schema. Tạo các map riêng cho core, fragile, bridge/soft switch, heavy switch, split/merge và case kết hợp. Với mỗi map, ghi trong bảng dưới một chuỗi action ngắn và kết quả mong đợi; không cần tự chứng minh đường tối ưu bằng tay. Solver phải replay path qua `Board.transition` để xác nhận thắng.

## Tổng quan bộ map

| Level | File | Kích thước | Cơ chế | Mô tả |
|---|---|---|---|---|
| 1 | `level_1.json` | 6×10 | Core | Đường đi cơ bản, void hai bên, không cơ chế đặc biệt |
| 2 | `level_2.json` | 8×12 | Core | Bản đồ rộng hơn, void ở 4 góc tạo đường vòng |
| 3 | `level_3.json` | 9×12 | Core | Đường đi hình chữ S, void xen kẽ trái/phải |
| 4 | `level_4.json` | 6×12 | Fragile | Hai ô fragile chắn giữa đường, khối không được đứng lên |
| 5 | `level_5.json` | 8×14 | Fragile | Hai dải fragile 3 ô, void ở góc ép đường đi qua vùng nguy hiểm |
| 6 | `level_6.json` | 7×9 | Soft switch + Bridge | Một cầu đóng chắn giữa, cần đạp soft switch để mở |
| 7 | `level_7.json` | 11×13 | 2× Soft switch + 2× Bridge | Hai tầng cầu đóng, phải mở lần lượt từ dưới lên |
| 8 | `level_8.json` | 9×10 | Heavy switch + Bridge | Cầu đóng, phải **đứng** lên heavy switch mới kích hoạt |
| 9 | `level_9.json` | 10×13 | Heavy + Fragile + Bridge | Heavy switch + fragile gần đường đi + cầu đóng |
| 10 | `level_10.json` | 9×10 | Split switch | Khối tách thành 2 cube, cần merge lại để thắng |
| 11 | `level_11.json` | 11×13 | Split + Bridge | Split đồng thời mở cầu, merge rồi đi qua cầu |
| 12 | `level_12.json` | 14×14 | Heavy + Soft + Fragile + 2× Bridge | Tổng hợp: 2 cầu, heavy + soft switch, 2 ô fragile |

## Chi tiết từng map

### Level 1 — Core cơ bản
- **Grid**: 6×10, void hai bên, floor ở giữa tạo đường chéo
- **Start**: `[1,1]` → **Goal**: `[4,7]`
- **Cơ chế**: Chỉ có `.` và `#`

### Level 2 — Core mở rộng
- **Grid**: 8×12, void ở góc trên-trái và dưới-phải
- **Start**: `[2,1]` → **Goal**: `[5,9]`
- **Cơ chế**: Chỉ có `.` và `#`, đường đi dài hơn level 1

### Level 3 — Đường chữ S
- **Grid**: 9×12, void xen kẽ trái-phải tạo hình chữ S
- **Start**: `[0,2]` → **Goal**: `[7,10]`
- **Cơ chế**: Chỉ void, phải rẽ nhiều lần

### Level 4 — Fragile đơn giản
- **Grid**: 6×12, 2 ô `F` ở hàng 2 (cols 4–5)
- **Start**: `[1,1]` → **Goal**: `[4,8]`
- **Cơ chế**: Khối nằm đi qua fragile được, khối đứng thì rơi

### Level 5 — Fragile kép
- **Grid**: 8×14, hai dải `FFF` ở hàng 2 và hàng 5, void ở góc
- **Start**: `[1,1]` → **Goal**: `[6,11]`
- **Cơ chế**: Hai vùng fragile ép đường đi phải tính toán orientation

### Level 6 — Soft switch + cầu
- **Grid**: 7×9, cầu `b1` đóng chắn hàng 3 (3 ô)
- **Start**: `[4,3]` → **Goal**: `[1,7]`
- **Cơ chế**: Soft switch `S` ở `[5,0]` — bất kỳ phần khối đè lên đều kích hoạt → mở cầu b1
- **Trình tự**: Đi xuống chạm switch → cầu mở → đi ngược lên qua cầu → goal

### Level 7 — Hai cầu tuần tự
- **Grid**: 11×13, hai cầu đóng ở hàng 3 và hàng 7
- **Start**: `[10,5]` → **Goal**: `[0,6]`
- **Cơ chế**: Switch `s2` ở `[9,9]` mở cầu b2 (hàng 7), switch `s1` ở `[5,2]` mở cầu b1 (hàng 3)
- **Trình tự**: Mở b2 → đi qua → mở b1 → đi qua → goal

### Level 8 — Heavy switch
- **Grid**: 9×10, cầu đóng ở hàng 3 (2 ô)
- **Start**: `[7,7]` → **Goal**: `[1,3]`
- **Cơ chế**: Heavy switch `H` ở `[7,2]` — khối phải **đứng** trên ô mới kích hoạt
- **Trình tự**: Di chuyển chính xác để đứng lên H → mở cầu → đi qua → goal

### Level 9 — Heavy + Fragile
- **Grid**: 10×13, cầu đóng ở hàng 4 (2 ô), fragile ở `[1,2]` và `[7,9]`
- **Start**: `[8,7]` → **Goal**: `[1,9]`
- **Cơ chế**: Heavy switch + fragile gần đường đi
- **Trình tự**: Đứng lên H ở `[8,2]` → mở cầu → đi qua, tránh đứng trên fragile

### Level 10 — Split switch
- **Grid**: 9×10, toàn floor trừ split switch `X` ở `[4,4]`
- **Start**: `[1,4]` → **Goal**: `[7,4]`
- **Cơ chế**: Khối đứng lên X → tách thành 2 cube ở `[5,2]` và `[5,6]`
- **Trình tự**: Đi tới X → split → dùng SWITCH để xen kẽ điều khiển → đưa 2 cube cạnh nhau → merge → đi tới goal

### Level 11 — Split + Bridge
- **Grid**: 11×13, cầu đóng ở hàng 7 (5 ô), split switch ở `[4,6]`
- **Start**: `[2,6]` → **Goal**: `[9,6]`
- **Cơ chế**: X split đồng thời toggle cầu b1
- **Trình tự**: Đứng lên X → split + mở cầu → merge 2 cube → đi qua cầu → goal

### Level 12 — Tổng hợp
- **Grid**: 14×14, hai cầu đóng ở hàng 4 và hàng 8, fragile ở `[2,8]` và `[10,8]`
- **Start**: `[12,2]` → **Goal**: `[1,11]`
- **Cơ chế**: Heavy switch `H` ở `[10,2]` mở cầu b2, Soft switch `S` ở `[6,2]` mở cầu b1
- **Trình tự**: Đứng lên H → mở b2 → đi qua → chạm S → mở b1 → đi qua → tránh fragile → goal

## Ghi chú

- Map TXT có thể là bản phác thảo; map dùng chạy chương trình phải chuyển sang JSON theo `docs/API.md` và được validate.
- Giữ tập benchmark cố định cho cả bốn solver.
- Ký hiệu grid: `#` void, `.` floor, `F` fragile, `S` soft switch, `H` heavy switch, `X` split switch.
- Bridge cells trong grid đánh dấu `.` (floor); trạng thái đóng/mở do metadata `bridges` quyết định.
- Switch positions trong grid dùng ký hiệu tương ứng (`S`/`H`/`X`); chi tiết trong metadata `switches`.
