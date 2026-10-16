# Checklist kiểm thử thủ công — thành viên 5

Map và kết quả mong đợi do thành viên 4 chuẩn bị; thành viên 5 chạy và ghi lại kết quả thực tế. Thành viên 3 rà các map special tiles. Chỉ đánh dấu sau khi tính năng được triển khai.

| Ca thử | Map | Thao tác | Kết quả mong đợi | Thực tế / lỗi |
|---|---|---|---|---|
| Lăn cơ bản | | | Khối đổi vị trí/hướng đúng | |
| Rơi khỏi board | | | Animation rơi, game over | |
| Đứng trên goal | | | Win; nằm qua goal chưa win | |
| Fragile | | | Đứng thì rơi, nằm thì an toàn | |
| Soft/heavy switch | | | Cầu đổi đúng điều kiện | |
| Split + SWITCH + merge | | | Đổi cube active và tự ghép khi kề | |
| Solve replay | | | Mọi bước hợp lệ và kết thúc ở goal | |
| Restart/chọn level | | | Reset đầy đủ khối/cầu/UI | |

Khi báo lỗi, ghi: map, mode, các action đã bấm, kết quả mong đợi, kết quả thực tế, ảnh/video nếu cần và commit đang test. Báo cáo PDF và video cần nội dung chuyên môn từ mỗi thành viên; thành viên 5 tổng hợp, chỉnh định dạng và dựng demo.
