// Cấu hình chung của frontend.
// - Khi chạy ở máy local (localhost / 127.0.0.1): tự động gọi http://127.0.0.1:8000/api
// - Khi deploy lên Vercel: điền URL Backend thực tế vào PRODUCTION_API_URL bên dưới
//   (ví dụ: "https://agile-backend.onrender.com/api"). Nếu để trống sẽ gọi "/api" cùng tên miền.
const PRODUCTION_API_URL = "";

const IS_LOCALHOST = ["localhost", "127.0.0.1"].includes(window.location.hostname);

const CONFIG = {
  API_BASE_URL: IS_LOCALHOST
    ? "http://127.0.0.1:8000/api"
    : (PRODUCTION_API_URL || `${window.location.origin}/api`),
  APP_NAME: "Agile Workspace",
};
