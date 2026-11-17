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

## Chạy Server Backend

```powershell
cd backend
..\..\venv2\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

- Tài liệu Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`
- Auth routes: `http://localhost:8000/api/auth/...`

