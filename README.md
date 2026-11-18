# Agile Task Management

Ứng dụng quản lý dự án theo mô hình Kanban, gồm backend FastAPI/MySQL và frontend HTML/CSS/JavaScript.

## Chức năng chính

- Đăng ký, đăng nhập, cập nhật hồ sơ và đăng nhập Google OAuth2.
- Quản lý dự án, thành viên, lời mời, danh sách và công việc.
- Checklist, bình luận, tệp đính kèm, thông báo và nhật ký hoạt động.
- Quản trị người dùng và theo dõi thống kê dự án.

## Chạy lần đầu

1. Cài Python 3.10+ và MySQL 8+, hoặc dùng Docker nếu đã cài Docker Compose.
2. Tạo `.env` tại thư mục gốc từ `.env.example`, sau đó điền `DB_PASSWORD` và tạo `SECRET_KEY` ngẫu nhiên. Cấu hình database mặc định là `agile_task_management`.
3. Tạo database:
   - MySQL cài trực tiếp: chạy `backend/sql/init.sql` bằng MySQL Workbench.
   - Docker: từ thư mục `backend/`, chạy `docker compose up -d`.
4. Từ thư mục gốc, tạo và kích hoạt môi trường ảo rồi cài dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   ```

5. Khởi chạy backend từ thư mục `backend/`:

   ```powershell
   uvicorn app.main:app --reload
   ```

   API docs: http://127.0.0.1:8000/docs

   Health check: http://127.0.0.1:8000/api/health

6. Mở `frontend/index.html` bằng VS Code Live Server. Mặc định frontend chạy ở http://127.0.0.1:5500; API URL được cấu hình trong `frontend/js/config.js`.

Google OAuth là tùy chọn. Cấu hình `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` và đăng ký callback URI tương ứng với `GOOGLE_REDIRECT_URI` trong Google Cloud Console.

Xem hướng dẫn chi tiết ở [backend/README.md](backend/README.md) và [frontend/README.md](frontend/README.md).
