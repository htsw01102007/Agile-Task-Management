const message = document.getElementById("oauth-message");
const loginLink = document.getElementById("oauth-login-link");
const fragment = new URLSearchParams(window.location.hash.slice(1));
const query = new URLSearchParams(window.location.search);
const accessToken = fragment.get("access_token");
const refreshToken = fragment.get("refresh_token");
const error = query.get("error");

history.replaceState(null, "", window.location.pathname);

if (error) {
  message.textContent = error;
  loginLink.hidden = false;
} else if (!accessToken || !refreshToken) {
  message.textContent = "Không nhận được thông tin đăng nhập từ Google. Vui lòng thử lại.";
  loginLink.hidden = false;
} else {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
  window.location.replace("../index.html");
}
