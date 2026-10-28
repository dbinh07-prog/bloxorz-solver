# Bộ 12 map: bàn khuyết và đảo

Bộ map có 8 màn dạng bàn vuông/chữ nhật bị khoét, xẻ khe hoặc đục lỗ, xen kẽ 4 màn nhiều đảo. Các màn đảo là **3, 8, 10, 12**. Điểm đầu cách xa ô thoát; không thu nhỏ bàn thành một đường duy nhất.

| Màn | Tên | Kiểu | Ít bước nhất | Nội dung |
|---|---|---|---:|---|
| 1 | Bàn khuyết góc | Bàn khuyết | 10 | Bàn liền rộng, khuyết góc và có lỗ nhỏ ở giữa. |
| 2 | Khe chữ U | Bàn khuyết | 18 | Bàn chữ nhật xẻ khe, phải tìm đường vòng và chỉnh tư thế. |
| 3 | Vòng quanh bốn đảo | Nhiều đảo | 22 | Các đảo nối vòng, đích ở đảo khác. |
| 4 | Khe fragile | Bàn khuyết | 26 | Bàn chữ nhật bị cắt ngang; phải nằm qua dải fragile. |
| 5 | Cửa cầu bên hông | Bàn khuyết | 30 | Bàn bị xẻ dọc, soft switch mở cửa cầu duy nhất. |
| 6 | Vòng tới nút nặng | Bàn khuyết | 33 | Bàn có vách khuyết và heavy switch; phải đứng đúng vị trí để mở cầu. |
| 7 | Bàn ba dải | Bàn khuyết | 42 | Các dải sàn lớn ngăn bằng khe, kết hợp heavy toggle và fragile. |
| 8 | Hai chốt, hai cầu | Nhiều đảo | 46 | Heavy và soft ở các đảo khác nhau, mở hai cầu. |
| 9 | Buồng tách khối | Bàn khuyết | 48 | Tách vào các ngách trong lỗ bàn; hai cube mở đường cho nhau, ghép lại rồi bấm heavy. |
| 10 | Mở cầu rồi tách khối | Nhiều đảo | 50 | Giữ bố cục nhiều đảo và hai cube phối hợp mở cầu. |
| 11 | Buồng fragile và đường vòng | Bàn khuyết | 54 | Bàn khuyết có buồng tách, fragile, heavy và đường thoát vòng. |
| 12 | Quần đảo tổng hợp | Nhiều đảo | 62 | Giữ màn đảo tổng hợp với soft/heavy, cầu, fragile và split/merge. |

Số bước trên là lời giải ít hành động nhất theo BFS/IDS, có tính SWITCH. UCS/A* tối thiểu tổng cost nên có thể chọn đường khác hoặc nhiều bước hơn. Độ khó còn phụ thuộc bố cục và cơ chế, không chỉ số bước.

## Thử các cơ chế

- Màn 4: fragile bắt buộc.
- Màn 5–8: soft/heavy, cầu và toggle.
- Màn 9 và 11: tách vào buồng bên trong bàn lớn; cube nhỏ bấm soft, sau khi ghép mới đứng lên heavy để mở đường thoát. Màn 11 còn có fragile.
- Màn 10: nhiều đảo, hai cube mở cầu cho nhau.
- Màn 12: màn đảo tổng hợp đủ cơ chế.

## Kiểm tra và benchmark

Tất cả 12 map có lời giải và đường đi đã được phát lại qua `Board.transition` để xác nhận thắng. Những công tắc/fragile/SWITCH cần thiết đã được thử cấm riêng; khi cấm thì không còn lời giải. BFS và IDS khớp số bước, UCS và A* khớp tổng cost.

Màn 3, 8, 10, 12 giữ nguyên dữ liệu của bộ đảo trước; tám màn còn lại đã chạy lại cả bốn solver. Các số thời gian chạy kiểm tra ngoài repo không thay cho benchmark chính thức.

Giữ nguyên heuristic, thuật toán và cách đo. IDS có thể chờ lâu trên các màn lớn, nhất là lúc bật đo bộ nhớ. Sau khi đổi map, chạy lại `python run_experiments.py`; không so trực tiếp với CSV của bộ cũ.

`example_basic.json` vẫn giữ nguyên để thử RIGHT, RIGHT.

## Ký hiệu

`#`: vực; `.`: sàn; `F`: fragile; `S`: soft; `H`: heavy; `X`: split. Cầu và công tắc được nối bằng metadata `bridges`/`switches`. Tọa độ `[row, col]` tính từ 0.

<details>
<summary>Lời giải BFS tham khảo</summary>

U/D/L/R = UP/DOWN/LEFT/RIGHT; C = SWITCH.

- Màn 1: `R R R R D R D R D R`
- Màn 2: `D D R R R D D R R U U U R R D R D D`
- Màn 3: `R R R R R R D R D D D D D D L U L L L L L L`
- Màn 4: `D R R U R U R R R R D D R D D D L L D L D L L L L L`
- Màn 5: `U U U U U U L U L L L D D D D R D R R R R R U U U R U R U R`
- Màn 6: `D D D D R D D R D L D U U U U U U R R R R R R D R R D D D D D R R`
- Màn 7: `R R R R R R R U R L D L L L L U L D L D D R R D R R R U R R R D D L L L L L L D L D`
- Màn 8: `R D D R R R R R R R R U R R R R U R L D L L L L D L D D D D D D D L U L L L L L U L D R R D`
- Màn 9: `D R R D D D C D D L L D L C R R R U D L U R D D L U R D D D R R R R U R R D D D L D L U L D L L`
- Màn 10: `D L U L D R R R R R R R R U D L L L L L L L D D D D D D D L U R D L R R C L L L L L U L C R R R R D`
- Màn 11: `D R R D D D L U R D L D D D C D D L L D L C R R R U D L U R D D L U R D D D R R R R U R R D D D L D L U L D`
- Màn 12: `R D D R R R R R R R R U R R R R U R L D L L L L D L D D D D D D D L U L L L L L U L D R R D R R C L L L L L U L C R R R R D`

</details>
