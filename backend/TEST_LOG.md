# Test log

## Thông tin chạy test

- Ngày chạy: 2026-11-23
- Phạm vi: API đăng ký/đăng nhập, hồ sơ, dự án và phân quyền admin.
- Môi trường: pytest, FastAPI `TestClient`, SQLite tạm trong bộ nhớ; không kết nối MySQL và không dùng dữ liệu ứng dụng.
- Lệnh: `Set-Location backend; .\venv\Scripts\python.exe -m pytest .\tests\test_api.py -q`
- Kết quả: **16 passed, 0 failed**.
- Cảnh báo: 3 cảnh báo deprecated từ Starlette/httpx, Authlib/httpx và cấu hình Pydantic hiện có; không làm test thất bại.

## Các trường hợp kiểm thử

| ID | Trường hợp | Kết quả mong đợi | Kết quả | Bug / đã sửa |
|---|---|---|---|---|
| AUTH-01 | Đăng ký với dữ liệu hợp lệ | `201`, không trả hash mật khẩu | Pass | Không phát hiện |
| AUTH-02 | Đăng ký với email sai định dạng | `422` | Pass | Không phát hiện |
| AUTH-03 | Đăng ký với username sai định dạng | `422` | Pass | Không phát hiện |
| AUTH-04 | Đăng ký với mật khẩu yếu | `422` | Pass | Không phát hiện |
| AUTH-05 | Đăng ký email đã tồn tại, khác chữ hoa/thường | `409` | Pass | Không phát hiện |
| AUTH-06 | Đăng nhập bằng email | `200`, cấp access token | Pass | Không phát hiện |
| AUTH-07 | Đăng nhập bằng username | `200`, cấp access token | Pass | Không phát hiện |
| AUTH-08 | Đăng nhập với mật khẩu sai | `401` | Pass | Không phát hiện |
| AUTH-09 | Xem hồ sơ khi chưa đăng nhập | `401` | Pass | Không phát hiện |
| AUTH-10 | Xem và cập nhật hồ sơ khi đã đăng nhập | `200`, thông tin được cập nhật | Pass | Không phát hiện |
| AUTH-11 | Cập nhật hồ sơ với họ tên rỗng | `422` | Pass | Không phát hiện |
| PROJ-01 | Tạo dự án hợp lệ và xem danh sách | `201`; dự án xuất hiện trong danh sách | Pass | Không phát hiện |
| PROJ-02 | Tạo dự án với tên rỗng | `422` | Pass | Không phát hiện |
| PROJ-03 | Ngày kết thúc trước ngày bắt đầu | `400` | Pass | Không phát hiện |
| PROJ-04 | Tạo dự án khi chưa đăng nhập | `401` | Pass | Không phát hiện |
| ADMIN-01 | Admin xem tổng quan; user thường bị từ chối; khách chưa đăng nhập bị từ chối | Lần lượt `200`, `403`, `401` | Pass | Không phát hiện |

## Tổng kết bug

- Bug chức năng phát hiện: **0**.
- Bug đã sửa: **Không có**.
- Lần chạy đầu từ thư mục gốc không tìm thấy package `app`; chạy lại từ thư mục `backend` theo đúng import path thành công. Đây là cách gọi pytest, không phải bug của ứng dụng.
