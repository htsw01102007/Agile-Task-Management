const loginForm = document.getElementById("login-form");
const loginSubmit = document.getElementById("login-submit");
const passwordInput = document.getElementById("password");
const togglePwBtn = document.getElementById("toggle-login-pw");
const googleLoginBtn = document.getElementById("google-login-btn");
const oauthErrorBanner = document.getElementById("oauth-error-banner");

function redirectAfterLogin() {
  const requestedPath = new URLSearchParams(window.location.search).get("next");
  if (requestedPath && requestedPath !== "/index.html" && requestedPath !== "index.html") {
    const destination = new URL(requestedPath, window.location.href);
    if (destination.origin === window.location.origin) {
      window.location.assign(`${destination.pathname}${destination.search}${destination.hash}`);
      return;
    }
  }
  window.location.assign("../index.html");
}

// Kiểm tra lỗi trả về từ Google OAuth2 (nếu có ?error= trên URL)
const urlParams = new URLSearchParams(window.location.search);
const urlError = urlParams.get("error");
if (urlError) {
  if (oauthErrorBanner) {
    oauthErrorBanner.textContent = urlError;
    oauthErrorBanner.hidden = false;
  }
  showToast(urlError, "error");
  urlParams.delete("error");
  const cleanSearch = urlParams.toString();
  window.history.replaceState({}, document.title, `${window.location.pathname}${cleanSearch ? `?${cleanSearch}` : ""}`);
}

googleLoginBtn?.addEventListener("click", () => {
  const next = new URLSearchParams(window.location.search).get("next");
  if (next) localStorage.setItem("oauth_next", next);
  const frontendBase = new URL("..", window.location.href).href.replace(/\/$/, "");
  window.location.assign(`${CONFIG.API_BASE_URL}/auth/google/login?frontend_url=${encodeURIComponent(frontendBase)}`);
});

togglePwBtn?.addEventListener("click", () => {
  const isPw = passwordInput.type === "password";
  passwordInput.type = isPw ? "text" : "password";
  togglePwBtn.innerHTML = iconSvg(isPw ? "eyeOff" : "eye");
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginSubmit.disabled = true;
  loginSubmit.textContent = "Đang xác thực…";
  try {
    const formData = new FormData(loginForm);
    const result = await api.post("/auth/login", {
      identifier: formData.get("identifier"),
      password: formData.get("password"),
    });
    localStorage.setItem("access_token", result.access_token);
    localStorage.setItem("refresh_token", result.refresh_token);
    redirectAfterLogin();
  } catch (error) {
    if (!applyApiErrorsToForm(loginForm, error)) {
      showToast(error.message, "error");
    }
  } finally {
    loginSubmit.disabled = false;
    loginSubmit.textContent = "Đăng nhập vào Workspace →";
  }
});
