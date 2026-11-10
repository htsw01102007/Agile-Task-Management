# Task Project Management API - Module Authentication

Backend API xây dựng bằng FastAPI, SQLAlchemy, MySQL, PyJWT, Authlib (Google OAuth2).

## 1. Cấu trúc thư mục

```
project1111/
├── app/
│   ├── api/
│   │   └── auth.py               # Router cho Login, Register, Me, Google OAuth2
│   ├── core/
│   │   ├── config.py             # Cấu hình biến môi trường pydantic-settings
│   │   ├── database.py           # Kết nối MySQL SQLAlchemy Engine, Session
│   │   ├── deps.py               # Dependency get_current_user, require_role kiểm tra JWT
│   │   └── security.py           # Bcrypt hashing & PyJWT encode/decode
│   ├── models/
│   │   ├── user.py               # SQLAlchemy model bảng users
│   │   └── oauth_account.py      # SQLAlchemy model bảng oauth_accounts (lưu token Google)
│   ├── schemas/
│   │   └── auth.py               # Pydantic schemas: RegisterRequest, LoginRequest, UserOut, TokenResponse
│   ├── services/
│   │   └── auth_service.py       # Logic nghiệp vụ xác thực
│   ├── main.py                   # FastAPI Application & Middlewares
│   └── seed.py                   # Script khởi tạo tài khoản mẫu
├── tests/
│   └── test_auth.py              # Pytest kiểm thử tự động
├── task_project_management.sql   # File DDL cơ sở dữ liệu MySQL
├── requirements.txt              # Thư viện phụ thuộc
├── GOOGLE_OAUTH_SETUP.md         # Hướng dẫn chi tiết tạo Google OAuth2 Client ID & Secret
├── pytest.ini                    # Cấu hình pytest
└── .env                          # Cấu hình môi trường
```

## 2. Các Endpoint Authentication

- `POST /auth/register`: Đăng ký tài khoản (Username, Email, Mật khẩu mạnh, Họ tên)
- `POST /auth/login`: Đăng nhập bằng Email hoặc Username + Mật khẩu -> Trả về JWT
- `GET /auth/me`: Lấy thông tin user hiện tại (Header `Authorization: Bearer <token>`)
- `GET /auth/google/login`: Bắt đầu luồng đăng nhập Google OAuth2
- `GET /auth/google/callback`: Nhận mã ủy quyền từ Google, tạo/liên kết tài khoản và trả JWT về Frontend qua URL fragment `#access_token=...`

## 3. Chạy Server Backend

```powershell
cd project1111
..\venv2\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 4. Tài khoản kiểm thử sẵn có

- **Admin**: `superadmin` / `superadmin@taskflow.vn` - Mật khẩu: `SuperAdmin@123`
- **User**: `testuser` / `testuser@taskflow.vn` - Mật khẩu: `User@123456`

