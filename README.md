# Bloxorz Solver

<div align="center">
  <img width="1268" height="712" alt="Bloxorz-Solver" src="https://github.com/user-attachments/assets/4c3905ef-a848-4018-babd-7951577546d6" />
  <p><em>Giao diện Menu chính của ứng dụng Bloxorz-Solver.</em></p>
</div>

## Giới thiệu
**Bloxorz Solver** là đồ án thuộc môn Cơ sở Trí tuệ Nhân tạo, được phát triển thành một ứng dụng Desktop 3D sử dụng ngôn ngữ Python và thư viện đồ họa Ursina Engine. 

Dự án không chỉ tái hiện lại tựa game giải đố Bloxorz với đầy đủ các cơ chế nâng cao (gạch dễ vỡ, cầu đóng/mở, công tắc nặng/mềm, và đặc biệt là cơ chế chẻ khối), mà còn tích hợp hệ thống Trí tuệ Nhân tạo để tự động tìm kiếm đường đi tối ưu. 

Đặc điểm nổi bật của dự án:
- **Giao diện 3D trực quan:** Hệ thống cho phép người dùng quan sát bàn cờ đa góc độ, chơi thủ công (Manual Play) hoặc xem AI diễn hoạt lại từng bước giải (Solver Replay).
- **Thuật toán đa dạng:** Tích hợp cả thuật toán tìm kiếm mù (BFS, IDS) và tìm kiếm có thông tin (UCS, A* với hàm Heuristic tự thiết kế) để giải quyết các ma trận bản đồ từ cơ bản đến phức tạp.
- **Hệ thống bản đồ mở rộng:** Dữ liệu màn chơi được lưu trữ độc lập dưới định dạng JSON, cho phép dễ dàng thiết kế và thử nghiệm các level mới.

## Hướng dẫn cài đặt và chạy benchmark

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

## Link video demo

Để có cái nhìn trực quan về cách ứng dụng hoạt động, bao gồm môi trường đồ họa 3D, gameplay thực tế và các thuật toán AI tự động giải màn chơi, mời các bạn xem video demo dưới đây:

[![Video Demo](https://img.shields.io/badge/YouTube-Xem_Video_Demo-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/watch?v=Vtyy6W9HIpM)

👉 **Link trực tiếp:** [https://www.youtube.com/watch?v=Vtyy6W9HIpM](https://www.youtube.com/watch?v=Vtyy6W9HIpM)
