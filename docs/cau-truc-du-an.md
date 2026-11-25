# Phân tích cấu trúc thư mục & tệp dự án `Agile-Task-Management`

Tài liệu tóm tắt ngắn gọn chức năng của từng thư mục và từng tệp trong dự án **Agile Task Management** (Backend: FastAPI + SQLAlchemy + MySQL; Frontend: HTML/CSS/Vanilla JS).

---

## 1. Thư mục gốc (`Agile-Task-Management/`)

| Tệp / Thư mục | Tác dụng |
|---|---|
| `README.md` | Hướng dẫn tổng quan, cài đặt và chạy dự án. |
| `requirements.txt` | Danh sách thư viện Python ở mức gốc. |
| `.env.example` | Mẫu biến môi trường cho dự án. |
| `.gitignore` | Danh sách tệp/thư mục bỏ qua khi commit Git. |
| `.gitattributes` | Quy tắc xử lý xuống dòng (LF/CRLF) và thuộc tính Git. |
| `backend/` | Toàn bộ mã nguồn API server, DB, SQL và bộ test. |
| `frontend/` | Toàn bộ giao diện web tĩnh (HTML, CSS, JS). |
| `docs/` | Tài liệu phân tích và đặc tả luồng nghiệp vụ. |

---

## 2. Tài liệu (`docs/`)

| Tệp | Tác dụng |
|---|---|
| `luong-moi-thanh-vien.md` | Mô tả chi tiết luồng mời thành viên vào dự án (gửi/chấp nhận/từ chối lời mời). |
| `cau-truc-du-an.md` | Tài liệu này — phân tích vai trò từng thư mục và tệp trong dự án. |

---

## 3. Backend (`backend/`)

### 3.1. Tệp cấu hình & tiện ích ở `backend/`

| Tệp / Thư mục | Tác dụng |
|---|---|
| `README.md` | Hướng dẫn cài đặt, cấu hình và chạy riêng phần backend. |
| `requirements.txt` | Các package Python backend cần cài (FastAPI, SQLAlchemy, PyMySQL, PyJWT, pytest...). |
| `docker-compose.yml` | Khởi chạy nhanh MySQL 8.0 bằng Docker. |
| `.env` | Biến môi trường thực tế khi chạy local (DB, JWT, OAuth, SMTP...). |
| `.env.example` | Mẫu biến môi trường cho backend. |
| `.gitignore` | Bỏ qua `.env`, `__pycache__`, `uploads/`, v.v. |
| `check_db.py` | Script nhỏ kiểm tra kết nối trực tiếp tới MySQL. |
| `uploads/` | Thư mục lưu tệp đính kèm (attachment) người dùng tải lên. |
| `app/main.py` | Điểm khởi chạy FastAPI: cấu hình CORS/Session, kết nối DB, tự tạo bảng/migration nhỏ lúc startup và gắn toàn bộ router. |
| `app/__init__.py` | Đánh dấu `app` là Python package. |

---

### 3.2. `backend/app/core/` — Cấu hình, bảo mật & hạ tầng dùng chung

| Tệp | Tác dụng |
|---|---|
| `__init__.py` | Export các thành phần dùng chung của `core`. |
| `config.py` | Đọc & validate biến môi trường (`Settings`: DB, JWT, CORS, OAuth, SMTP, upload...). |
| `deps.py` | Dependency FastAPI xác thực JWT (`get_current_user`) và kiểm tra vai trò hệ thống (`require_role`). |
| `security.py` | Băm/kiểm tra mật khẩu, tạo & giải mã JWT access/refresh token. |
| `permissions.py` | Kiểm tra quyền truy cập ở mức dự án & task (owner/admin/member/viewer, ghi/xóa/khôi phục). |
| `rate_limit.py` | Bộ giới hạn tần suất gọi API theo IP/tài khoản (in-memory) chống spam/brute-force. |
| `email.py` | Gửi email (đặt lại mật khẩu, v.v.). |
| `email_policy.py` | Chuẩn hóa định dạng email và chặn domain email rác (disposable email). |
| `social.py` | Xử lý luồng đăng nhập Google OAuth 2.0 và xác thực ID token. |
| `time.py` | Hàm chuẩn hóa thời gian UTC (`utc_now_naive`, `as_utc_naive`). |
| `ws_manager.py` | Quản lý kết nối WebSocket theo dự án/người dùng và gửi sự kiện realtime từ code đồng bộ. |

---

### 3.3. `backend/app/db/` — Kết nối cơ sở dữ liệu

| Tệp | Tác dụng |
|---|---|
| `__init__.py` | Khởi tạo package `db`. |
| `session.py` | **(Đang dùng chính)** Tạo SQLAlchemy `engine`, `SessionLocal`, `Base` và dependency `get_db()`. |
| `database.py` | *(Bản cũ/trùng vai trò)* Kết nối SQLAlchemy cho nhóm model/router cũ (`entities.py`). |

---

### 3.4. `backend/app/models/` — Mô hình bảng dữ liệu (SQLAlchemy ORM)

| Tệp | Tác dụng |
|---|---|
| `__init__.py` | Import tất cả model để SQLAlchemy đăng ký metadata khi `create_all`. |
| `common.py` | Kiểu cột `ID` tương thích MySQL/SQLite và `TimestampMixin` (`created_at`, `updated_at`). |
| `user.py` | Bảng `users` (tài khoản, mật khẩu, vai trò hệ thống, `token_version`). |
| `oauth_account.py` | Bảng `oauth_accounts` (liên kết tài khoản Google OAuth). |
| `password_reset_token.py` | Bảng `password_reset_tokens` (token đặt lại mật khẩu có hạn dùng). |
| `revoked_token.py` | Bảng `revoked_tokens` (danh sách JWT đã thu hồi khi đăng xuất). |
| `project.py` | Bảng `projects` (thông tin dự án, trạng thái lưu trữ/xóa mềm). |
| `project_member.py` | Bảng `project_members` (thành viên và vai trò trong dự án). |
| `project_invitation.py` | Bảng `project_invitations` (lời mời tham gia dự án kèm token & trạng thái). |
| `list.py` | Bảng `lists` (cột Kanban trong dự án). |
| `task.py` | Bảng `tasks` (công việc, độ ưu tiên, hạn hoàn thành, vị trí, xóa mềm). |
| `task_assignee.py` | Bảng trung gian `task_assignees` (người được giao task). |
| `label.py` | Bảng `labels` (nhãn phân loại màu sắc theo dự án). |
| `task_label.py` | Bảng trung gian `task_labels` (gắn nhãn cho task). |
| `checklist.py` | Bảng `checklist_items` (đang dùng chính với `routers/checklist.py`). |
| `checklist_item.py` | Định nghĩa bảng `checklist_items` phiên bản khác (dùng cùng `entities.py`). |
| `comment.py` | Bảng `comments` (bình luận task, hỗ trợ sửa & xóa mềm). |
| `attachment.py` | Bảng `attachments` (metadata tệp đính kèm của task). |
| `notification.py` | Bảng `notifications` (thông báo gửi tới người dùng). |
| `notification_enums.py` | Enum các loại thông báo (`task_assigned`, `comment_added`, `project_invited`...). |
| `activity_log.py` | Bảng `activity_logs` (nhật ký hoạt động trong dự án). |
| `activity_enums.py` | Enum loại thực thể (`EntityType`) và hành động (`ActivityAction`). |
| `entities.py` | *(Bản cũ/tham chiếu)* Gộp định nghĩa các bảng lõi kế thừa từ `db/database.py`. |

---

### 3.5. `backend/app/schemas/` — Validate dữ liệu vào/ra (Pydantic)

| Tệp | Tác dụng |
|---|---|
| `__init__.py` | Khởi tạo package `schemas`. |
| `common.py` | `ORMModel` nền và `UserBrief` dùng chung. |
| `auth.py` | Schema đăng ký, đăng nhập, token, đổi/quên mật khẩu, hồ sơ người dùng, quản trị user. |
| `project.py` | Schema tạo/sửa/trả về dự án và thống kê dashboard. |
| `project_member.py` | Schema thành viên dự án, đổi vai trò, chuyển quyền sở hữu. |
| `project_invitation.py` | Schema tạo/hiển thị lời mời dự án. |
| `list.py` | Schema tạo/sửa/sắp xếp cột Kanban. |
| `task.py` | Schema tạo/sửa/di chuyển/lọc/trả về task. |
| `label.py` | Schema tạo/sửa/gắn nhãn. |
| `checklist.py` | Schema tạo/sửa/tóm tắt checklist item (đang dùng chính). |
| `checklist_item.py` | *(Bản cũ)* Schema checklist item đi kèm `common.py`. |
| `comment.py` | Schema tạo/sửa/trả về bình luận. |
| `attachment.py` | Schema trả về thông tin tệp đính kèm. |
| `notification.py` | Schema thông báo và trạng thái đã đọc. |
| `activity_log.py` | Schema hiển thị lịch sử hoạt động. |
| `board.py` | *(Bản cũ)* Schema cho API Kanban board cũ (`routers/projects.py`, `routers/tasks.py`). |

---

### 3.6. `backend/app/crud/` — Tầng xử lý nghiệp vụ & truy vấn DB

| Tệp | Tác dụng |
|---|---|
| `__init__.py` | Export các hàm CRUD chính. |
| `auth.py` | Nghiệp vụ đăng ký, đăng nhập, cấp/refresh/thu hồi token, quên & đặt lại mật khẩu. |
| `user.py` | Truy vấn & tạo mới người dùng (thường và đăng nhập mạng xã hội). |
| `oauth_account.py` | Liên kết & đăng nhập bằng tài khoản Google OAuth. |
| `project.py` | Tạo dự án kèm chủ sở hữu, chuyển quyền sở hữu, tạo/tra cứu/hash token lời mời. |
| `notification.py` | Tạo thông báo cho người được giao task khi có bình luận mới. |
| `board.py` | *(Bản cũ)* Xử lý CRUD board/list/task cho router `projects.py` & `tasks.py`. |
| `comment.py` | *(Bản cũ)* Xử lý CRUD bình luận cho router `comments.py`. |

---

### 3.7. `backend/app/routers/` — Định nghĩa API Endpoints

#### Các router đang được gắn và chạy chính (trong `routers/__init__.py` & `main.py`):

| Tệp | Prefix / Nhóm API | Tác dụng |
|---|---|---|
| `__init__.py` | — | Gom và export toàn bộ router đang hoạt động. |
| `health.py` | `/health` | Kiểm tra tình trạng server & kết nối DB. |
| `auth.py` | `/auth` | Đăng ký, đăng nhập, đăng xuất, refresh token, OAuth, quên/đổi mật khẩu, hồ sơ cá nhân. |
| `admin.py` | `/admin/users` | Quản trị người dùng hệ thống (thống kê, danh sách, tạo/sửa/khóa tài khoản). |
| `project.py` | `/projects` | CRUD dự án, cột (list), thống kê tổng quan & dashboard. |
| `project_members.py` | `/projects/{project_id}/members` | Quản lý thành viên dự án, đổi vai trò, rời/xóa thành viên, chuyển quyền owner. |
| `invitations.py` | `/projects/{project_id}/invitations` | Tạo, xem danh sách và hủy lời mời trong dự án. |
| `invitations_public.py` | `/invitations` | Xem lời mời của bản thân (`/me`), chấp nhận (`/accept/{token}`) và từ chối (`/decline/{token}`). |
| `task.py` | `/projects/{project_id}/tasks` & `/tasks` | CRUD task, di chuyển cột/vị trí, giao việc, xóa mềm/khôi phục và `my-tasks`. |
| `label.py` | `/projects/{project_id}/labels` | Quản lý nhãn và gắn/gỡ nhãn trên task. |
| `checklist.py` | `/projects/{project_id}/tasks/{task_id}/checklist` | Quản lý các mục việc nhỏ (checklist) và tiến độ hoàn thành của task. |
| `comment.py` | `/projects/{project_id}/tasks/{task_id}/comments` | Xem, thêm, sửa, xóa bình luận trên task. |
| `attachment.py` | `/projects/{project_id}/tasks/{task_id}/attachments` | Upload (kiểm tra MIME/dung lượng), tải xuống và xóa tệp đính kèm. |
| `notification.py` | `/notifications` | Lấy danh sách thông báo, đếm chưa đọc, đánh dấu đã đọc. |
| `activity_log.py` | `/projects/{project_id}/activity-logs` | Xem lịch sử thao tác trong dự án. |
| `ws.py` | `/ws` | Kết nối WebSocket realtime theo dự án (`/ws/projects/{id}`) và thông báo cá nhân (`/ws/notifications`). |

#### Các router cũ (không được gắn trong `main.py`):

| Tệp | Tác dụng |
|---|---|
| `projects.py` | Router dự án/board phiên bản cũ (dùng `crud/board.py`). |
| `tasks.py` | Router sửa/xóa task phiên bản cũ (dùng `crud/board.py`). |
| `comments.py` | Router bình luận phiên bản cũ (dùng `crud/comment.py`). |

---

### 3.8. `backend/sql/` — Script cơ sở dữ liệu MySQL

| Tệp | Tác dụng |
|---|---|
| `init.sql` | Script khởi tạo toàn bộ schema DB `task_project_management` (hỗ trợ `password_hash` nullable cho OAuth). |
| `task_project_management.sql` | Bản đầy đủ schema SQL của hệ thống quản lý dự án & công việc. |
| `patch_comments_edit_columns.sql` | Bản vá bổ sung cột `edited_at`, `deleted_by` vào bảng `comments` cho DB cũ. |
| `patch_oauth_accounts.sql` | Bản vá tạo thêm bảng `oauth_accounts` cho DB cũ. |

---

### 3.9. `backend/tests/` — Bộ kiểm thử tự động (Pytest)

| Tệp | Tác dụng |
|---|---|
| `conftest.py` | Fixture dùng chung (tạo DB test, FastAPI `TestClient`, tài khoản mẫu). |
| `test_app_config.py` | Test cấu hình môi trường & kiểm tra thiết lập production. |
| `test_auth.py` | Test luồng đăng ký, đăng nhập, refresh, logout, mật khẩu. |
| `test_projects_and_members.py` | Test CRUD dự án, thành viên và phân quyền trong dự án. |
| `test_invitations.py` | Test gửi, chấp nhận, từ chối, hủy và chống trùng lời mời. |
| `test_tasks_and_features.py` | Test task, list, checklist, comment, label, attachment, notification, activity log. |
| `test_rate_limits.py` | Test cơ chế giới hạn tốc độ gọi API. |
| `test_security_hardening.py` | Test các kịch bản bảo mật (quyền truy cập, token bị thu hồi, MIME upload, v.v.). |

---

## 4. Frontend (`frontend/`)

### 4.1. Tệp gốc, tài nguyên & CSS

| Tệp | Tác dụng |
|---|---|
| `README.md` | Hướng dẫn chạy giao diện frontend. |
| `index.html` | Trang chủ / Dashboard tổng quan các dự án. |
| `check.html` | Trang kiểm tra nhanh trạng thái kết nối tới Backend API (`/health`). |
| `assets/images/logo.svg` | Biểu tượng logo ứng dụng. |
| `css/style.css` | Toàn bộ stylesheet giao diện cho ứng dụng. |

---

### 4.2. `frontend/js/` — Thư viện JS dùng chung

| Tệp | Tác dụng |
|---|---|
| `config.js` | Cấu hình `API_BASE_URL` (tự nhận diện `localhost` hoặc URL production). |
| `api.js` | Lớp gọi HTTP `fetch` tới backend, tự đính kèm Bearer token và refresh token khi hết hạn. |
| `layout.js` | Dựng khung giao diện chung (sidebar, topbar, tìm kiếm nhanh toàn cục, chuông thông báo). |
| `utils.js` | Bộ icon SVG tối giản và các hàm tiện ích dùng chung (format ngày, escape HTML, toast...). |
| `app.js` | *(Bản cũ/SPA mẫu)* Logic giao diện đơn trang cũ (không dùng bởi các trang trong `pages/`). |

---

### 4.3. `frontend/pages/` & `frontend/js/pages/` — Các trang chức năng

Mỗi trang `.html` trong `frontend/pages/` đi kèm một tệp logic `.js` cùng tên trong `frontend/js/pages/`:

| Cặp tệp (`.html` + `.js`) | Tác dụng |
|---|---|
| `index.html` + `home.js` | Trang chủ hiển thị danh sách dự án, thống kê và tạo dự án mới. |
| `login.html` + `login.js` | Đăng nhập bằng tài khoản/mật khẩu hoặc Google OAuth 2.0. |
| `register.html` + `register.js` | Đăng ký tài khoản mới. |
| `forgot-password.html` + `forgot-password.js` | Yêu cầu gửi email/token đặt lại mật khẩu. |
| `reset-password.html` + `reset-password.js` | Nhập mật khẩu mới từ link/token khôi phục. |
| `oauth-callback.html` + `oauth-callback.js` | Nhận kết quả trả về sau khi đăng nhập OAuth, lưu token và chuyển hướng. |
| `project.html` + `project.js` | Giao diện chính của dự án: bảng Kanban/Danh sách, chi tiết task, checklist, bình luận, tệp đính kèm, thành viên, nhãn, lịch sử hoạt động & WebSocket realtime. |
| `my-tasks.html` + `my-tasks.js` | Xem và lọc toàn bộ công việc được giao cho người dùng hiện tại across mọi dự án. |
| `invitations.html` + `invitations.js` | Danh sách lời mời tham gia dự án gửi tới người dùng hiện tại. |
| `invitation.html` + `invitation.js` | Trang xử lý chấp nhận hoặc từ chối một lời mời cụ thể qua link/token. |
| `profile.html` + `profile.js` | Xem/cập nhật thông tin cá nhân và đổi mật khẩu. |
| `admin-users.html` + `admin-users.js` | Trang quản trị người dùng dành cho admin hệ thống. |
| `items.html` + `items.js` | *(Trang mẫu CRUD)* Ví dụ tham khảo thao tác Thêm/Sửa/Xóa từ bộ khung ban đầu. |

---

## 5. Ghi chú nhanh về tệp đang hoạt động vs. tệp cũ/mẫu

- **Đang chạy chính**: `backend/app/main.py` → `db/session.py` → các router số ít (`project.py`, `task.py`, `comment.py`, `checklist.py`, ...) và toàn bộ các trang thực tế trong `frontend/pages/`.
- **Tệp cũ / mẫu còn giữ lại**: `db/database.py`, `models/entities.py`, `models/checklist_item.py`, `schemas/board.py`, `schemas/checklist_item.py`, `crud/board.py`, `crud/comment.py`, `routers/projects.py`, `routers/tasks.py`, `routers/comments.py`, `frontend/js/app.js`, `frontend/pages/items.html`, `frontend/js/pages/items.js`.
