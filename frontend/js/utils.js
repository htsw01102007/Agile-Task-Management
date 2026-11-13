// Các hàm tiện ích dùng chung cho nhiều trang.

// Chống XSS: luôn dùng hàm này khi chèn dữ liệu người dùng nhập vào innerHTML
function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

// 45000 -> "45.000 ₫"
function formatMoney(value) {
  return Number(value).toLocaleString("vi-VN") + " ₫";
}

// "2026-11-04T09:30:00" -> "09:30 4/11/2026"
function formatDateTime(value) {
  const d = new Date(value);
  return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) + " " +
    d.toLocaleDateString("vi-VN");
}

// Hiện thông báo nhỏ ở góc màn hình. type: "success" | "error"
function showToast(message, type = "success") {
  let container = document.getElementById("toasts");
  if (!container) {
    container = document.createElement("div");
    container.id = "toasts";
    container.setAttribute("role", "status");
    container.setAttribute("aria-live", "polite");
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${type === "error" ? "error" : "success"}`;
  const icon = document.createElement("span");
  icon.className = "t-ic";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = type === "error" ? "!" : "✓";
  const text = document.createElement("span");
  text.className = "t-msg";
  text.textContent = message;
  const close = document.createElement("button");
  close.className = "t-x";
  close.type = "button";
  close.setAttribute("aria-label", "Đóng thông báo");
  close.textContent = "×";
  close.addEventListener("click", () => toast.remove());
  toast.append(icon, text, close);
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4200);
}
