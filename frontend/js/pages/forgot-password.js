const forgotForm = document.getElementById("forgot-form");
const forgotSubmit = document.getElementById("forgot-submit");
const forgotResult = document.getElementById("forgot-result");

forgotForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  forgotSubmit.disabled = true;
  forgotSubmit.textContent = "Đang gửi…";
  forgotResult.textContent = "";
  try {
    const result = await api.post("/auth/forgot-password", {
      email: new FormData(forgotForm).get("email"),
    });
    forgotResult.textContent = result.message;
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    forgotSubmit.disabled = false;
    forgotSubmit.textContent = "Gửi hướng dẫn";
  }
});
