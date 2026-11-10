# HƯỚNG DẪN CẤU HÌNH GOOGLE OAUTH2 (CHO DỰ ÁN TASK PROJECT MANAGEMENT)

Tài liệu này hướng dẫn chi tiết từng bước tạo **Client ID** và **Client Secret** trên Google Cloud Console để tích hợp chức năng **Đăng nhập bằng tài khoản Google (OAuth2)** vào dự án backend `project1111`.

---

## BƯỚC 1: Truy Cập Google Cloud Console & Tạo Project

1. Truy cập vào trang quản lý Google Cloud: [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Đăng nhập bằng tài khoản Google của bạn.
3. Ở thanh menu trên cùng (bên cạnh logo Google Cloud), nhấn vào danh sách dự án và chọn **NEW PROJECT** (Dự án mới).
4. Điền:
   - **Project Name**: `Task Project Management` (hoặc tên bất kỳ bạn muốn).
   - Nhấn **CREATE**.
5. Chờ vài giây rồi chọn đúng dự án vừa tạo ở menu trên cùng.

---

## BƯỚC 2: Cấu Hình Màn Hình Đồng Ý OAuth (OAuth Consent Screen)

Google yêu cầu khai báo màn hình đồng ý trước khi tạo Client ID:

1. Ở thanh menu bên trái, tìm đến **APIs & Services** -> chọn **OAuth consent screen** (hoặc truy cập nhanh: [https://console.cloud.google.com/apis/credentials/consent](https://console.cloud.google.com/apis/credentials/consent)).
2. Tại mục **User Type**:
   - Chọn **External** (Bên ngoài).
   - Nhấn **CREATE**.
3. Điền thông tin cơ bản:
   - **App name**: `Task Project Management`
   - **User support email**: Chọn email của bạn.
   - **Developer contact information**: Điền email của bạn.
   - Nhấn **SAVE AND CONTINUE**.
4. Mục **Scopes** (Phạm vi):
   - Nhấn **ADD OR REMOVE SCOPES**.
   - Tích chọn 3 quyền cơ bản:
     - `.../auth/userinfo.email` (Xem địa chỉ email chính)
     - `.../auth/userinfo.profile` (Xem thông tin cá nhân cơ bản)
     - `openid` (Xác thực OpenID Connect)
   - Nhấn **UPDATE** -> Nhấn **SAVE AND CONTINUE**.
5. Mục **Test users** (Người dùng thử nghiệm):
   - Nhấn **ADD USERS**.
   - Nhập chính email Google mà bạn dùng để đăng nhập test thử nghiệm.
   - Nhấn **SAVE AND CONTINUE** -> Nhấn **BACK TO DASHBOARD**.

---

## BƯỚC 3: Tạo Khóa OAuth 2.0 Client ID

1. Vào mục **APIs & Services** -> chọn **Credentials** (hoặc truy cập: [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)).
2. Nhấn nút **+ CREATE CREDENTIALS** ở trên cùng -> chọn **OAuth client ID**.
3. Điền các trường chính xác như sau:
   - **Application type**: Chọn `Web application`.
   - **Name**: `TaskFlow Web Client` (hoặc tên tùy thích).
   - **Authorized JavaScript origins**:
     - Nhấn **+ ADD URI**
     - Nhập: `http://localhost:5173` (địa chỉ Frontend React/Vite)
     - Nhấn **+ ADD URI** thêm một dòng nữa: `http://localhost:8000` (địa chỉ Backend FastAPI)
   - **Authorized redirect URIs** *(CỰC KỲ QUAN TRỌNG - Bắt buộc phải chính xác từng ký tự)*:
     - Nhấn **+ ADD URI**
     - Nhập chính xác:
       ```
       http://localhost:8000/auth/google/callback
       ```
4. Nhấn **CREATE**.
5. Màn hình sẽ hiện ra một hộp thoại chứa:
   - **Your Client ID** (dạng `xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com`)
   - **Your Client Secret** (dạng `GOCSPX-xxxxxxxxxxxxxxxxxxxx`)
   *(Bạn có thể nhấn nút copy hoặc tải file JSON về máy).*

---

## BƯỚC 4: Cập Nhật Vào Dự Án Backend `project1111`

1. Mở file `.env` tại thư mục gốc: `F:\New folder\.vscode\API\project1111\.env`.
2. Dán 2 giá trị bạn vừa nhận được từ Google vào:

```env
# Google OAuth2 Credentials
GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

3. Lưu file `.env`.
4. Khởi động lại server backend:

```powershell
cd "F:\New folder\.vscode\API\project1111"
..\venv2\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## BƯỚC 5: Kiểm Tra Luồng Đăng Nhập

1. Mở trình duyệt truy cập:
   ```
   http://localhost:8000/auth/google/login
   ```
2. Trình duyệt sẽ tự động chuyển hướng sang trang chọn tài khoản của Google.
3. Sau khi bạn chọn tài khoản và nhấn "Tiếp tục" (hoặc Cho phép), Google sẽ redirect về endpoint `http://localhost:8000/auth/google/callback`.
4. Backend sẽ tự động:
   - Lấy email, họ tên, avatar và `google_sub`.
   - Tạo hoặc liên kết tài khoản trong bảng `users` và `oauth_accounts` của MySQL.
   - Cấp chuỗi **JWT Token** và chuyển tiếp về Frontend kèm hash `#access_token=...`.

