const filtersForm = document.getElementById("user-filters");
const usersBody = document.getElementById("users-body");
const pageLabel = document.getElementById("users-page");
const pageSize = 20;
let page = 1;
let users = [];

async function loadAdminProfile() {
  const card = document.getElementById("admin-profile-card");
  try {
    const user = await api.get("/auth/me");
    if (user.system_role !== "admin") {
      document.getElementById("create-user-toggle").hidden = true;
      card.innerHTML = '<strong>Trang này chỉ dành cho quản trị viên.</strong> <a href="profile.html">Xem hồ sơ tài khoản</a>';
      usersBody.innerHTML = '<tr><td colspan="5" class="text-error">Tài khoản hiện tại không có quyền quản trị.</td></tr>';
      return false;
    }
    document.getElementById("create-user-toggle").hidden = false;
    document.getElementById("admin-profile-name").textContent = user.full_name || "Quản trị viên";
    document.getElementById("admin-profile-email").textContent = user.email || "Chưa có email";
    document.getElementById("admin-profile-avatar").textContent = layoutInitials(user.full_name || user.email || "A");
    return true;
  } catch (error) {
    document.getElementById("create-user-toggle").hidden = true;
    card.innerHTML = `<span class="text-error">${escapeHtml(error.message)}</span>`;
    usersBody.innerHTML = `<tr><td colspan="5" class="text-error">${escapeHtml(error.message)}</td></tr>`;
    return false;
  }
}

async function loadUsers() {
  usersBody.innerHTML = '<tr><td colspan="5">Đang tải…</td></tr>';
  const form = new FormData(filtersForm);
  const params = { page, size: pageSize };
  const q = String(form.get("q") || "").trim();
  const active = form.get("is_active");
  if (q) params.q = q;
  if (active) params.is_active = active;
  try {
    users = await api.get("/admin/users", params);
    usersBody.innerHTML = users.length ? users.map((user) => `
      <tr data-user-id="${user.id}">
        <td><strong>${escapeHtml(user.full_name)}</strong><small>${escapeHtml(user.email)} · @${escapeHtml(user.username)}</small></td>
        <td>${escapeHtml(user.system_role)}</td><td><span class="role-badge ${user.is_active ? "status-active" : "status-inactive"}">${user.is_active ? "Đang hoạt động" : "Đã khóa"}</span></td>
        <td>${user.last_login_at ? escapeHtml(formatDateTime(user.last_login_at)) : "Chưa đăng nhập"}</td>
        <td><button class="btn btn-small" type="button" data-edit-user="${user.id}">Sửa tên</button> ${user.system_role === "admin" ? "—" : `<button class="btn btn-small ${user.is_active ? "btn-danger" : ""}" type="button" data-toggle-user="${user.id}" data-next-status="${!user.is_active}">${user.is_active ? "Khóa" : "Mở khóa"}</button>`}</td>
      </tr>`).join("") : '<tr><td colspan="5" class="muted">Không tìm thấy tài khoản.</td></tr>';
    pageLabel.textContent = `Trang ${page}`;
    document.getElementById("users-prev").disabled = page <= 1;
    document.getElementById("users-next").disabled = users.length < pageSize;
  } catch (error) {
    usersBody.innerHTML = `<tr><td colspan="5" class="text-error">${escapeHtml(error.message)}</td></tr>`;
    document.getElementById("users-prev").disabled = true;
    document.getElementById("users-next").disabled = true;
  }
}

filtersForm.addEventListener("submit", (event) => {
  event.preventDefault();
  page = 1;
  loadUsers();
});
document.getElementById("users-prev").addEventListener("click", () => { if (page > 1) { page -= 1; loadUsers(); } });
document.getElementById("users-next").addEventListener("click", () => { if (users.length === pageSize) { page += 1; loadUsers(); } });
usersBody.addEventListener("click", async (event) => {
  const toggleButton = event.target.closest("[data-toggle-user]");
  const editButton = event.target.closest("[data-edit-user]");
  if (toggleButton) {
    const user = users.find((item) => item.id === Number(toggleButton.dataset.toggleUser));
    const nextStatus = toggleButton.dataset.nextStatus === "true";
    if (!user || !confirm(`${nextStatus ? "Mở khóa" : "Khóa"} tài khoản ${user.email}?`)) return;
    toggleButton.disabled = true;
    try {
      await api.patch(`/admin/users/${user.id}/status`, { is_active: nextStatus });
      showToast(nextStatus ? "Đã mở khóa tài khoản" : "Đã khóa tài khoản");
      await loadUsers();
    } catch (error) {
      toggleButton.disabled = false;
      showToast(error.message, "error");
    }
  } else if (editButton) {
    const user = users.find((item) => item.id === Number(editButton.dataset.editUser));
    if (!user) return;
    const fullName = prompt("Nhập họ tên mới:", user.full_name);
    if (fullName === null || !fullName.trim()) return;
    editButton.disabled = true;
    try {
      await api.put(`/admin/users/${user.id}`, { full_name: fullName.trim() });
      showToast("Đã cập nhật họ tên");
      await loadUsers();
    } catch (error) {
      editButton.disabled = false;
      showToast(error.message, "error");
    }
  }
});

const createUserPanel = document.getElementById("create-user-panel");
document.getElementById("create-user-toggle").addEventListener("click", () => {
  createUserPanel.hidden = !createUserPanel.hidden;
});
document.getElementById("create-user-cancel").addEventListener("click", () => {
  createUserPanel.hidden = true;
  document.getElementById("create-user-form").reset();
});
document.getElementById("create-user-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form));
  const submitButton = form.querySelector('[type="submit"]');
  submitButton.disabled = true;
  try {
    await api.post("/admin/users", data);
    form.reset();
    createUserPanel.hidden = true;
    page = 1;
    filtersForm.reset();
    showToast("Đã tạo tài khoản thành viên");
    await loadUsers();
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    submitButton.disabled = false;
  }
});

loadAdminProfile().then((isAdmin) => {
  if (isAdmin) loadUsers();
});
