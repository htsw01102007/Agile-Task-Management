# Agile Task Management

Ứng dụng quản lý dự án Agile với frontend HTML/CSS/JavaScript thuần và backend FastAPI + MySQL. Frontend hiện có:

- Dashboard chỉ hiển thị số liệu sau đăng nhập; tạo/sửa/lưu trữ dự án
- Bảng Kanban từ API: CRUD task/list, kéo thả, hạn chót, độ ưu tiên, người thực hiện, checklist, bình luận và tệp đính kèm
- Quản lý thành viên, vai trò và lời mời; đăng ký/đăng nhập; trang Việc của tôi
- Quản trị người dùng (tổng quan số liệu toàn hệ thống, tài khoản mới, tạo/tìm kiếm/sửa/khóa tài khoản); tài khoản admin đầu tiên được khởi tạo từ `.env`
- Hồ sơ cá nhân hiển thị email, tên đăng nhập và cho phép cập nhật họ tên
- Layout chung, sidebar, thông báo toast và gọi API qua Axios

## 1. Cấu trúc thư mục

```
frontend/
├── index.html             # Dashboard sau khi đăng nhập
├── pages/
│   ├── project.html       # Bảng Kanban của dự án
│   ├── login.html         # Đăng nhập
│   ├── register.html      # Đăng ký
│   ├── my-tasks.html      # Việc được giao
│   ├── invitations.html   # Lời mời của tài khoản
│   ├── invitation.html    # Chấp nhận/từ chối lời mời
│   ├── profile.html       # Hồ sơ cá nhân
│   └── admin-users.html   # Quản trị tài khoản
├── css/
│   └── style.css          # Style chung, đổi màu ở :root
├── js/
│   ├── config.js          # API_BASE_URL: địa chỉ backend
│   ├── api.js             # axios instance + api.get / post / put / delete
│   ├── utils.js           # escapeHtml, formatMoney, showToast...
│   ├── layout.js          # Header, sidebar và trạng thái đăng nhập
│   └── pages/             # Mỗi trang 1 file JS riêng
│       ├── home.js
│       └── items.js
└── assets/images/         # Ảnh, logo, icon
```

## 2. Chạy frontend

**Bước 1: cấu hình và chạy backend.** Làm theo `backend/README.md`. Đặt `ADMIN_EMAIL`, `ADMIN_USERNAME` và `ADMIN_PASSWORD` trong file `.env` ở thư mục gốc; mật khẩu admin cần ít nhất 8 ký tự, có chữ hoa, chữ thường và số. Admin được tạo tự động một lần khi backend khởi động, và mật khẩu không bị reset khi chạy lại.

**Bước 2: mở frontend bằng Live Server.** Trong VS Code, mở `frontend/index.html` bằng Live Server. Mặc định API nằm tại `http://127.0.0.1:8001/api`; có thể đổi trong `frontend/js/config.js`.

Đăng ký người dùng từ trang Đăng ký, hoặc đăng nhập admin bằng thông tin đã đặt trong `.env`. Dùng admin để quản lý tài khoản; tạo dự án và mời thành viên tại bảng dự án.

> Nhấp đúp mở thẳng file `index.html` (địa chỉ `file:///...`) thường vẫn chạy, nhưng hay gặp lỗi khó hiểu. Nên dùng Live Server.

## 3. Frontend nối với backend thế nào?

```
Trình duyệt (FE: 127.0.0.1:5500) --axios--> Backend FastAPI (127.0.0.1:8001/api) --> MySQL
```

- **axios** được nạp từ CDN bằng thẻ `<script>` ở cuối mỗi trang HTML (cần có mạng). Không cần `npm install`.
- Địa chỉ backend nằm ở **một chỗ duy nhất**: `js/config.js`
  ```js
  API_BASE_URL: "http://127.0.0.1:8001/api",
  ```
  Backend đổi cổng, hoặc deploy lên server, thì chỉ sửa dòng này.
- Mọi lời gọi API đều qua `js/api.js`. File này tạo sẵn 1 axios instance (`http`) có `baseURL`, và bọc thành các hàm trả về thẳng `response.data`:
  ```js
  try {
    const items = await api.get("/items");               // GET  /api/items
    const found = await api.get("/items", { q: "trà" }); // GET  /api/items?q=trà
    const item  = await api.post("/items", { name: "Trà đá", price: 5000 });
    await api.put(`/items/${item.id}`, { price: 6000 });
    await api.delete(`/items/${item.id}`);
  } catch (error) {
    showToast(error.message, "error");  // câu báo lỗi đã được dịch cho dễ đọc
    console.log(error.status);          // 404, 422, 500... hoặc 0 nếu không gọi được server
  }
  ```
- Trang bảng gọi `GET /projects/{id}` và `GET /projects/{id}/board`; nếu chưa có token, hãy đăng nhập ở trang **Đăng nhập**.
- `js/api.js` tự gửi `access_token` đã đăng nhập trong header `Authorization: Bearer ...`.
- Backend phải cho phép FE gọi (**CORS**). Base code backend đã bật sẵn (`CORS_ORIGINS=*` trong `backend/.env`).

## 4. Thêm trang mới (vd: trang Sản phẩm)

1. Copy `pages/items.html` thành `pages/products.html`, sửa `<title>` và nội dung HTML.
2. Copy `js/pages/items.js` thành `js/pages/products.js`, đổi `/items` thành `/products` (API của nhóm bạn).
3. Ở cuối `pages/products.html`, đổi `../js/pages/items.js` thành `../js/pages/products.js`.
4. Thêm link vào menu trong `js/layout.js`:
   ```js
   { href: "pages/products.html", label: "Sản phẩm" },
   ```

Lưu ý khi tạo trang:

- Trang trong `pages/` để `<body data-root="../">`; trang ở thư mục gốc để `data-root="./"`.
- Giữ thứ tự thẻ `<script>`: axios (CDN) → `config.js` → `api.js` → `utils.js` → `layout.js` → script riêng của trang.
- Khi chèn dữ liệu người dùng nhập vào `innerHTML`, luôn bọc bằng `escapeHtml(...)` để chống chèn mã độc (XSS).

## 5. Lỗi hay gặp

| Hiện tượng | Cách sửa |
|---|---|
| Không nhận được phản hồi từ backend | Trang Việc của tôi có nút **Kiểm tra backend** để thử `/api/health`; kiểm tra địa chỉ trong `js/config.js`, Uvicorn và CORS |
| "Backend chạy nhưng MySQL lỗi" | Xem mục *Lỗi hay gặp* trong `backend/README.md` |
| Console báo `axios is not defined` | Máy không có mạng nên không tải được axios từ CDN, hoặc thẻ `<script>` axios bị đặt sau `api.js` |
| Console (F12) báo `blocked by CORS policy` | Kiểm tra `CORS_ORIGINS` trong `backend/.env`, sửa xong nhớ chạy lại backend |
| Menu/header không hiện | Sai `data-root` ở thẻ `<body>`, hoặc sai đường dẫn file JS. Mở F12 → Console để xem lỗi |
| Sửa code mà trang không đổi | Tải lại cứng: `Ctrl + F5` |
