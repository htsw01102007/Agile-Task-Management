const registerForm = document.getElementById("register-form");
const registerSubmit = document.getElementById("register-submit");
const registerPwInput = document.getElementById("register-password");
const toggleRegisterPwBtn = document.getElementById("toggle-register-pw");
const googleRegisterBtn = document.getElementById("google-register-btn");
const pwBars = document.querySelectorAll("#register-pw-meter .pw-bar");
const pwHint = document.getElementById("register-pw-hint");

googleRegisterBtn?.addEventListener("click", () => {
  const frontendBase = new URL("..", window.location.href).href.replace(/\/$/, "");
  window.location.assign(`${CONFIG.API_BASE_URL}/auth/google/login?frontend_url=${encodeURIComponent(frontendBase)}`);
});

toggleRegisterPwBtn?.addEventListener("click", () => {
  const isPw = registerPwInput.type === "password";
  registerPwInput.type = isPw ? "text" : "password";
  toggleRegisterPwBtn.innerHTML = iconSvg(isPw ? "eyeOff" : "eye");
});

registerPwInput?.addEventListener("input", () => {
  const val = registerPwInput.value;
  let score = 0;
  if (val.length >= 8) score += 1;
  if (/[A-Z]/.test(val)) score += 1;
  if (/[a-z]/.test(val)) score += 1;
  if (/\d/.test(val)) score += 1;

  const tone = score <= 1 ? "active-weak" : score <= 3 ? "active-medium" : "active-strong";
  pwBars.forEach((bar, idx) => {
    bar.className = "pw-bar";
    if (val.length > 0 && idx < score) bar.classList.add(tone);
  });

  if (!val.length) {
    pwHint.textContent = "Cần ít nhất 8 ký tự, bao gồm chữ hoa (A-Z), chữ thường (a-z) và chữ số (0-9).";
  } else if (score < 4) {
    pwHint.textContent = `Độ mạnh mật khẩu: ${score}/4 tiêu chí đã đạt.`;
  } else {
    pwHint.textContent = "✓ Mật khẩu hợp lệ và đủ độ mạnh.";
  }
});

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!validateForm(registerForm)) return;
  const formData = new FormData(registerForm);
  const password = String(formData.get("password"));
  registerSubmit.disabled = true;
  registerSubmit.textContent = "Đang khởi tạo tài khoản…";
  try {
    await api.post("/auth/register", {
      full_name: String(formData.get("full_name")).trim(),
      email: String(formData.get("email")).trim(),
      username: String(formData.get("username")).trim(),
      password,
    });
    showToast("Đăng ký thành công. Chuyển tới trang đăng nhập…");
    window.setTimeout(() => window.location.assign("login.html"), 700);
  } catch (error) {
    if (!applyApiErrorsToForm(registerForm, error)) {
      showToast(error.message, "error");
    }
  } finally {
    registerSubmit.disabled = false;
    registerSubmit.textContent = "Hoàn tất đăng ký →";
  }
});
