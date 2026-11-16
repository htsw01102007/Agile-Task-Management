# Backend

Backend dùng FastAPI, SQLAlchemy, MySQL và JWT. Cấu hình được đọc từ file `.env` ở thư mục gốc dự án (cùng cấp với file này).

## Cài đặt

Từ thư mục gốc dự án, tạo `.env` từ `.env.example` và điền mật khẩu MySQL. Cơ sở dữ liệu mặc định là `agile_task_management`, trùng với schema trong `sql/init.sql`.

Tạo môi trường ảo và cài dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Tạo schema bằng một trong hai cách:

- MySQL cài trực tiếp: chạy `backend/sql/init.sql` bằng MySQL Workbench.
- Docker Compose: từ thư mục `backend/`, chạy `docker compose up -d`. Dịch vụ MySQL dùng cổng `3307`; đặt `DB_PORT=3307`, `DB_USER=app_user`, `DB_PASSWORD=app_password`, `DB_NAME=agile_task_management` trong file `.env` gốc.

Docker chỉ tự chạy `sql/init.sql` khi khởi tạo volume mới. Các file SQL patch/cũ không được chạy tự động. Nếu cần áp dụng migration cho database cũ, hãy xem nội dung script và sao lưu database trước khi chạy.

## Chạy và kiểm tra

Từ thư mục `backend/`:

```powershell
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

Nếu MySQL chưa sẵn sàng, API vẫn khởi động nhưng health check trả về lỗi `503` cho đến khi database kết nối được.

## Cấu hình

Các biến quan trọng trong `.env`:

| Biến | Giá trị mặc định / ghi chú |
|---|---|
| `DB_HOST`, `DB_PORT` | `127.0.0.1`, `3306` (Docker: `3307`) |
| `DB_USER`, `DB_PASSWORD` | Tài khoản MySQL của bạn |
| `DB_NAME` | `agile_task_management` |
| `SECRET_KEY` | Đặt một chuỗi ngẫu nhiên, dài và riêng cho môi trường |
| `FRONTEND_URL` | `http://127.0.0.1:5500` |
| `CORS_ORIGINS` | Danh sách origin phân cách bằng dấu phẩy, hoặc `*` khi phát triển |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Để trống nếu không dùng Google OAuth |
| `GOOGLE_REDIRECT_URI` | Callback backend đã đăng ký ở Google Cloud Console |

Sau khi sửa `.env`, khởi động lại backend. Cấu hình `FRONTEND_URL` phải là origin frontend, không thêm tên file; callback frontend là `/pages/oauth-callback.html`.

## Kiểm thử

Chạy từ thư mục gốc (sau khi đã cài `backend/requirements.txt` vào môi trường ảo):

```powershell
.\.venv\Scripts\python.exe -m compileall -q backend\app
.\.venv\Scripts\python.exe -m pytest -q backend\tests
```

Các test cấu hình không cần MySQL đang chạy.
