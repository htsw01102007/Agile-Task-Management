# Task Project Management API (Backend)

Cấu trúc thư mục được chuẩn hóa theo phong cách kiến trúc **Agile-Task-Management**:

```
backend/
├── app/
│   ├── core/           # Cấu hình hệ thống (config, security, deps)
│   ├── crud/           # Xử lý truy vấn CSDL và logic nghiệp vụ (auth, ...)
│   ├── db/             # Kết nối cơ sở dữ liệu SQLAlchemy (session, engine)
│   ├── models/         # SQLAlchemy Models (user, project, member, ...)
│   ├── routers/        # FastAPI Routers (/api/health, /api/auth, ...)
│   ├── schemas/        # Pydantic Schemas request/response
│   └── main.py         # Khởi động ứng dụng FastAPI
├── sql/
│   └── init.sql        # Script tạo cơ sở dữ liệu MySQL
├── .env                # Biến môi trường
├── .env.example        # Mẫu biến môi trường
├── docker-compose.yml  # Docker Compose cấu hình MySQL & Backend
└── requirements.txt    # Danh sách thư viện Python
```

## Chạy MySQL và Backend

Backend đọc cấu hình từ file `.env` ở thư mục gốc repository. Tạo file này từ mẫu và điền thông tin MySQL của bạn:

```powershell
Copy-Item .env.example .env
```

Điền `ADMIN_EMAIL`, `ADMIN_USERNAME` và `ADMIN_PASSWORD` trong `.env` để khởi tạo tài khoản quản trị đầu tiên. Mật khẩu phải có tối thiểu 8 ký tự, gồm chữ hoa, chữ thường và chữ số. Backend chỉ tạo tài khoản này một lần; chạy lại sẽ không ghi đè mật khẩu đã đổi. Nếu tài khoản có email **và** tên đăng nhập khớp chính xác với hai giá trị cấu hình nhưng chưa có quyền admin, backend sẽ cấp quyền admin cho tài khoản đó, giữ nguyên mật khẩu và hồ sơ hiện tại. Nếu chỉ một trong hai giá trị trùng tài khoản khác, backend sẽ dừng để tránh cấp nhầm quyền.

Nếu dùng MySQL cài trực tiếp, đảm bảo dịch vụ đang chạy và `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` trong `.env` trỏ đúng tới database. Nếu dùng Docker Compose để chạy MySQL:

```powershell
docker compose -f backend/docker-compose.yml up -d db
```

Sau đó mở PowerShell tại thư mục `backend`, cài dependencies (chỉ cần làm lần đầu) và chạy FastAPI:

```powershell
cd backend
py -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

- Tài liệu Swagger UI: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/api/health`
- Auth routes: `http://localhost:8001/api/auth/...`

Sau khi cập nhật mã backend, dừng tiến trình Uvicorn cũ bằng `Ctrl+C` rồi chạy lại lệnh trên. Chỉ giữ một backend ở cổng 8001 để frontend không vô tình gọi một tiến trình cũ. Có thể kiểm tra phiên bản API đang nạp tại `http://127.0.0.1:8001/docs`; phần quản trị có `GET /api/admin/users/summary`.

Frontend đặt API mặc định tại `http://127.0.0.1:8001/api` trong `frontend/js/config.js`. Mở `frontend/index.html` bằng Live Server; đăng ký tại trang Đăng ký hoặc đăng nhập tài khoản đã có để tải dashboard, danh sách dự án và bảng Kanban. Trang Việc của tôi có nút **Kiểm tra backend** để xác nhận API và MySQL có phản hồi.
