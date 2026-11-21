const resetForm = document.getElementById("reset-form");
const resetSubmit = document.getElementById("reset-submit");
const resetResult = document.getElementById("reset-result");
const resetToken = new URLSearchParams(window.location.search).get("token");

if (!resetToken) {
  resetForm.hidden = true;
  resetResult.textContent =
    "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.";
}

resetForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!resetToken) return;
  resetSubmit.disabled = true;
  resetSubmit.textContent = "Đang cập nhật…";
  try {
    const result = await api.post("/auth/reset-password", {
      token: resetToken,
      new_password: new FormData(resetForm).get("new_password"),
    });
    resetResult.textContent = result.message;
    resetForm.hidden = true;
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    resetSubmit.disabled = false;
    resetSubmit.textContent = "Cập nhật mật khẩu";
  }
});
