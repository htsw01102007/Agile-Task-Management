# Frontend

Giao diện dùng HTML, CSS và JavaScript thuần; không cần bước build.

## Chạy

1. Khởi động backend theo [backend/README.md](../backend/README.md).
2. Mở `frontend/index.html` bằng VS Code Live Server (mặc định http://127.0.0.1:5500).
3. Đặt địa chỉ backend trong `js/config.js` (`API_BASE_URL`, mặc định `http://127.0.0.1:8000/api`).

Không nên mở trang bằng `file://`; dùng web server tĩnh để các đường dẫn, OAuth callback và CORS hoạt động ổn định.

## Các trang

- `index.html`: tổng quan dự án và thống kê.
- `pages/login.html`, `pages/register.html`: đăng nhập, đăng ký; Google OAuth nếu backend đã cấu hình.
- `pages/project.html`: bảng dự án.
- `pages/my-tasks.html`, `pages/invitations.html`, `pages/profile.html`: việc được giao, lời mời và hồ sơ.
- `pages/admin-users.html`: quản trị tài khoản.

Các trang dùng chung `js/api.js` để gọi API. Access/refresh token được lưu trong `localStorage`; lỗi API được chuyển thành `ApiError` và hiển thị bằng `showToast`.

## Thêm trang

Đặt HTML trong `pages/`, dùng đường dẫn tài nguyên tương đối từ thư mục này (`../css/`, `../js/`). Nạp các script theo thứ tự: Axios, `config.js`, `api.js`, `utils.js`, `layout.js`, rồi script riêng của trang.

Khi render dữ liệu động bằng `innerHTML`, escape nội dung người dùng bằng `escapeHtml`; ưu tiên `textContent` khi không cần markup.
