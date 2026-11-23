const titleEl = document.getElementById("oauth-status-title");
const messageEl = document.getElementById("oauth-status-message");
const spinnerEl = document.getElementById("oauth-spinner");
const actionsEl = document.getElementById("oauth-actions");

function handleOAuthCallback() {
  const searchParams = new URLSearchParams(window.location.search);
  const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ""));

  const error = searchParams.get("error") || hashParams.get("error");
  const accessToken = hashParams.get("access_token") || searchParams.get("access_token");
  const refreshToken = hashParams.get("refresh_token") || searchParams.get("refresh_token");

  if (error) {
    if (spinnerEl) spinnerEl.hidden = true;
    if (titleEl) titleEl.textContent = "Đăng nhập Google chưa thành công";
    if (messageEl) {
      messageEl.textContent = error;
      messageEl.className = "status status-error";
    }
    if (actionsEl) actionsEl.hidden = false;
    showToast(error, "error");
    return;
  }

  if (accessToken) {
    localStorage.setItem("access_token", accessToken);
    if (refreshToken) localStorage.setItem("refresh_token", refreshToken);

    // Xóa token trên thanh địa chỉ trình duyệt để bảo mật
    window.history.replaceState({}, document.title, window.location.pathname);

    if (titleEl) titleEl.textContent = "✓ Đăng nhập Google thành công!";
    if (messageEl) messageEl.textContent = "Đang chuyển hướng vào không gian làm việc của bạn…";
    showToast("Đăng nhập bằng Google thành công!");

    const next = localStorage.getItem("oauth_next");
    localStorage.removeItem("oauth_next");

    window.setTimeout(() => {
      if (next && next !== "/index.html" && next !== "index.html") {
        const destination = new URL(next, window.location.href);
        if (destination.origin === window.location.origin) {
          window.location.assign(`${destination.pathname}${destination.search}${destination.hash}`);
          return;
        }
      }
      window.location.assign("../index.html");
    }, 500);
    return;
  }

  if (spinnerEl) spinnerEl.hidden = true;
  if (titleEl) titleEl.textContent = "Không tìm thấy thông tin xác thực";
  if (messageEl) {
    messageEl.textContent = "Phiên xác thực Google không trả về mã truy cập hợp lệ. Vui lòng thử đăng nhập lại.";
    messageEl.className = "status status-error";
  }
  if (actionsEl) actionsEl.hidden = false;
}

handleOAuthCallback();
