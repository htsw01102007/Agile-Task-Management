const registerForm = document.getElementById("register-form");
const registerSubmit = document.getElementById("register-submit");

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(registerForm);
  const password = String(formData.get("password"));
  if (password.length < 8 || !/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
    showToast("Mật khẩu cần có tối thiểu 8 ký tự, chữ hoa, chữ thường và số.", "error");
    return;
  }
  registerSubmit.disabled = true;
  try {
    await api.post("/auth/register", {
      full_name: String(formData.get("full_name")).trim(),
      email: String(formData.get("email")).trim(),
      username: String(formData.get("username")).trim(),
      password,
    });
    showToast("Đăng ký thành công. Vui lòng đăng nhập.");
    window.setTimeout(() => window.location.assign("login.html"), 700);
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    registerSubmit.disabled = false;
  }
});
