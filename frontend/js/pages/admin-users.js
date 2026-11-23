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
      card.innerHTML = '<strong>Trang này chỉ dành cho quản trị viên.</strong> <a class="btn btn-small" href="profile.html">Xem hồ sơ tài khoản</a>';
      usersBody.innerHTML = '<tr><td colspan="5" class="text-error">Tài khoản hiện tại không có quyền quản trị.</td></tr>';
      return false;
    }
    document.getElementById("create-user-toggle").hidden = false;
    document.getElementById("admin-profile-name").textContent = user.full_name || "Quản trị viên";
    document.getElementById("admin-profile-email").textContent = user.email || "Chưa có email";
    document.getElementById("admin-profile-avatar").textContent = layoutInitials(user.full_name || user.email || "A");

    try {
      const summary = await api.get("/admin/users/summary");
      const totalEl = document.getElementById("adm-stat-users");
      const activeEl = document.getElementById("adm-stat-active");
      const lockedEl = document.getElementById("adm-stat-locked");
      const projEl = document.getElementById("adm-stat-projects");
      if (totalEl) totalEl.textContent = summary.user_count;
      if (activeEl) activeEl.textContent = summary.active_user_count;
      if (lockedEl) lockedEl.textContent = Math.max(0, summary.user_count - summary.active_user_count);
      if (projEl) projEl.textContent = summary.project_count;
    } catch {}

    return true;
  } catch (error) {
    document.getElementById("create-user-toggle").hidden = true;
    card.innerHTML = `<span class="text-error">${escapeHtml(error.message)}</span>`;
    usersBody.innerHTML = `<tr><td colspan="5" class="text-error">${escapeHtml(error.message)}</td></tr>`;
    return false;
  }
}

async function loadUsers() {
  usersBody.innerHTML = '<tr><td colspan="5" class="muted">Đang tải danh sách thành viên…</td></tr>';
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
        <td>
          <div class="user-cell">
            <span class="avatar avatar-small">${escapeHtml(layoutInitials(user.full_name || user.email || "U"))}</span>
            <div>
              <strong>${escapeHtml(user.full_name)}</strong>
              <small>${escapeHtml(user.email)} · @${escapeHtml(user.username)}</small>
            </div>
          </div>
        </td>
        <td><span class="role-badge">${escapeHtml(user.system_role.toUpperCase())}</span></td>
        <td><span class="role-badge ${user.is_active ? "status-active" : "status-inactive"}">${user.is_active ? "● Đang hoạt động" : "⊘ Đã khóa"}</span></td>
        <td>${user.last_login_at ? escapeHtml(formatDateTime(user.last_login_at)) : '<span class="muted">Chưa đăng nhập</span>'}</td>
        <td>
          <button class="btn btn-small" type="button" data-edit-user="${user.id}">${iconSvg("edit")}<span>Sửa tên</span></button>
          ${user.system_role === "admin" ? "" : `<button class="btn btn-small ${user.is_active ? "btn-danger" : "btn-primary"}" type="button" data-toggle-user="${user.id}" data-next-status="${!user.is_active}">${user.is_active ? "Khóa tài khoản" : "Mở khóa"}</button>`}
        </td>
      </tr>`).join("") : '<tr><td colspan="5" class="muted">Không tìm thấy tài khoản nào khớp bộ lọc.</td></tr>';
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
    if (!user) return;
    const ok = await showConfirmModal({
      eyebrow: "TRẠNG THÁI TÀI KHOẢN",
      title: `${nextStatus ? "Mở khóa" : "Khóa"} tài khoản?`,
      message: `Bạn có chắc chắn muốn ${nextStatus ? "mở khóa" : "khóa"} quyền truy cập của tài khoản ${user.email}?`,
      confirmText: nextStatus ? "Mở khóa tài khoản" : "Khóa tài khoản",
      danger: !nextStatus,
    });
    if (!ok) return;
    toggleButton.disabled = true;
    try {
      await api.patch(`/admin/users/${user.id}/status`, { is_active: nextStatus });
      showToast(nextStatus ? "Đã mở khóa tài khoản" : "Đã khóa tài khoản");
      await loadAdminProfile();
      await loadUsers();
    } catch (error) {
      toggleButton.disabled = false;
      showToast(error.message, "error");
    }
  } else if (editButton) {
    const user = users.find((item) => item.id === Number(editButton.dataset.editUser));
    if (!user) return;
    const fullName = await showPromptModal({
      eyebrow: "QUẢN TRỊ NGƯỜI DÙNG",
      title: "Cập nhật họ và tên",
      description: `Chỉnh sửa họ tên hiển thị cho tài khoản ${user.email}.`,
      label: "Họ và tên hiển thị *",
      defaultValue: user.full_name,
      maxlength: 150,
      submitText: "Lưu họ tên",
      requiredMessage: "Vui lòng nhập họ và tên.",
    });
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
    showToast("Đã tạo tài khoản thành viên mới");
    await loadAdminProfile();
    await loadUsers();
  } catch (error) {
    if (!applyApiErrorsToForm(form, error)) {
      showToast(error.message, "error");
    }
  } finally {
    submitButton.disabled = false;
  }
});

loadAdminProfile().then((isAdmin) => {
  if (isAdmin) loadUsers();
});
