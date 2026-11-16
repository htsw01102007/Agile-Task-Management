const loginForm = document.getElementById("login-form");
const loginSubmit = document.getElementById("login-submit");
const googleLogin = document.getElementById("google-login");

googleLogin.addEventListener("click", () => {
  window.location.assign(`${CONFIG.API_BASE_URL}/auth/google/login`);
});

const oauthError = new URLSearchParams(window.location.search).get("error");
if (oauthError) showToast(oauthError, "error");

function redirectAfterLogin() {
  const requestedPath = new URLSearchParams(window.location.search).get("next");
  if (requestedPath) {
    const destination = new URL(requestedPath, window.location.origin);
    if (destination.origin === window.location.origin) {
      window.location.assign(`${destination.pathname}${destination.search}${destination.hash}`);
      return;
    }
  }
  window.location.assign("../index.html");
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginSubmit.disabled = true;
  loginSubmit.textContent = "Đang đăng nhập…";
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
    showToast(error.message, "error");
  } finally {
    loginSubmit.disabled = false;
    loginSubmit.textContent = "Đăng nhập";
  }
});
