const dashboardDate = document.getElementById("dashboard-date");
const dashboardContent = document.getElementById("dashboard-content");
const authPrompt = document.getElementById("dashboard-auth-prompt");
const projectCards = document.getElementById("project-cards");
const projectDialog = document.getElementById("project-dialog");
const projectForm = document.getElementById("project-form");
const projectStatusFilter = document.getElementById("project-status-filter");
const projectSearchInput = document.getElementById("project-search");
const viewGridBtn = document.getElementById("view-grid-btn");
const viewListBtn = document.getElementById("view-list-btn");

let projects = [];
let currentUser = null;
let editingProjectId = null;

if (dashboardDate) {
  dashboardDate.textContent = new Intl.DateTimeFormat("vi-VN", {
    weekday: "long",
    day: "numeric",
    month: "numeric",
    year: "numeric",
  }).format(new Date()).toUpperCase();
}

function projectStatusText(status) {
  return { active: "Đang hoạt động", completed: "Hoàn thành", archived: "Đã lưu trữ" }[status] || status;
}

function roleLabel(role) {
  return { owner: "Owner", manager: "Manager", member: "Member", viewer: "Viewer" }[role] || role || "Member";
}

function renderWorkspaceHealth() {
  const totalTasks = projects.reduce((acc, p) => acc + (p.task_count || 0), 0);
  const completedTasks = projects.reduce((acc, p) => acc + (p.completed_task_count || 0), 0);
  const overdueTasks = projects.reduce((acc, p) => acc + (p.overdue_task_count || 0), 0);
  const activeTasks = Math.max(0, totalTasks - completedTasks);

  const donePct = totalTasks ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const activePct = totalTasks ? Math.round((activeTasks / totalTasks) * 100) : 0;
  const overduePct = totalTasks ? Math.min(100, Math.round((overdueTasks / totalTasks) * 100)) : 0;

  const doneLabel = document.getElementById("health-done-label");
  const activeLabel = document.getElementById("health-active-label");
  const overdueLabel = document.getElementById("health-overdue-label");
  if (doneLabel) doneLabel.textContent = `${completedTasks}/${totalTasks} việc (${donePct}%)`;
  if (activeLabel) activeLabel.textContent = `${activeTasks} việc (${activePct}%)`;
  if (overdueLabel) overdueLabel.textContent = `${overdueTasks} việc`;

  const doneBar = document.getElementById("health-done-bar");
  const activeBar = document.getElementById("health-active-bar");
  const overdueBar = document.getElementById("health-overdue-bar");
  if (doneBar) doneBar.style.width = `${donePct}%`;
  if (activeBar) activeBar.style.width = `${activePct}%`;
  if (overdueBar) overdueBar.style.width = `${overduePct}%`;
}

function renderUpcomingTasks(myTasks = []) {
  const container = document.getElementById("upcoming-tasks-list");
  if (!container) return;
  const pending = myTasks.filter((t) => !t.completed_at).slice(0, 5);
  if (!pending.length) {
    container.innerHTML = '<p class="empty-state" style="padding:18px;">Tuyệt vời! Bạn không có công việc tồn đọng nào.</p>';
    return;
  }
  const priorityNames = { low: "Thấp", medium: "TB", high: "Cao", urgent: "Khẩn" };
  const projectMap = new Map(projects.map((p) => [p.id, p]));
  container.innerHTML = pending.map((t) => {
    const proj = projectMap.get(t.project_id);
    const due = t.due_date ? formatDateTime(t.due_date) : "Chưa đặt hạn";
    return `<a class="mini-task-item" href="pages/project.html?project=${t.project_id}&task=${t.id}">
      <span class="priority priority-${escapeHtml(t.priority)}">${escapeHtml(priorityNames[t.priority] || t.priority)}</span>
      <div class="mini-task-body">
        <strong>${escapeHtml(t.title)}</strong>
        <small>${escapeHtml(proj?.name || `Dự án #${t.project_id}`)} · ${escapeHtml(due)}</small>
      </div>
    </a>`;
  }).join("");
}

function renderProjects() {
  const statusFilter = projectStatusFilter?.value || "";
  const query = (projectSearchInput?.value || "").trim().toLocaleLowerCase("vi");
  const visibleProjects = projects.filter((project) => {
    const matchStatus = !statusFilter || project.status === statusFilter;
    const matchQuery = !query
      || project.name.toLocaleLowerCase("vi").includes(query)
      || (project.description || "").toLocaleLowerCase("vi").includes(query);
    return matchStatus && matchQuery;
  });

  if (!visibleProjects.length) {
    projectCards.innerHTML = `<p class="empty-state" style="grid-column: 1 / -1;">${projects.length ? "Không tìm thấy dự án nào khớp với bộ lọc hiện tại." : "Bạn chưa tham gia dự án nào."}${projects.length ? "" : '<br><span>Nhấn "Khởi tạo dự án mới" ở góc trên để bắt đầu.</span>'}</p>`;
    return;
  }
  projectCards.innerHTML = visibleProjects.map((project, index) => {
    const canManage = ["owner", "manager"].includes(project.user_role);
    const canDelete = project.user_role === "owner";
    const isArchived = project.status === "archived";
    const color = ["teal", "amber", "violet", "emerald"][index % 4];
    const rate = Math.round(project.completion_rate || 0);
    return `<article class="project-card project-entry">
      <a class="project-card-link" href="pages/project.html?project=${project.id}">
        <div class="project-card-top">
          <span class="project-mark ${color}">${escapeHtml(layoutInitials(project.name))}</span>
          <div class="project-badges">
            <span class="role-badge">${escapeHtml(roleLabel(project.user_role))}</span>
            <span class="project-status"><i class="${project.status === "active" ? "" : "status-inactive"}"></i>${escapeHtml(projectStatusText(project.status))}</span>
          </div>
        </div>
        <h3>${escapeHtml(project.name)}</h3>
        <p class="muted">${escapeHtml(project.description || "Chưa có mô tả chi tiết cho dự án này.")}</p>
        <div class="project-stats-pills">
          <span class="stat-pill">${iconSvg("columns")} <span>${project.task_count} công việc</span></span>
          <span class="stat-pill">${iconSvg("check")} <span>${project.completed_task_count || 0} hoàn thành</span></span>
          ${project.overdue_task_count > 0 ? `<span class="stat-pill overdue">${iconSvg("alert")} <span>${project.overdue_task_count} quá hạn</span></span>` : ""}
        </div>
        <div class="project-progress">
          <div><span>Tiến độ tổng thể</span><strong>${rate}%</strong></div>
          <progress value="${rate}" max="100"></progress>
        </div>
      </a>
      <div class="project-card-bottom">
        <span style="display:inline-flex;align-items:center;gap:5px;">${iconSvg("users")} <span>${project.member_count} thành viên</span></span>
        <span class="project-card-actions">
          ${isArchived ? `
            ${canManage ? `<button class="btn btn-small btn-primary" type="button" data-action="unarchive" data-project-id="${project.id}">Khôi phục</button>` : ""}
            ${canDelete ? `<button class="btn btn-small btn-danger" type="button" data-action="delete" data-project-id="${project.id}">Xoá</button>` : ""}
          ` : `
            ${canManage ? `<button class="btn btn-small" type="button" data-action="edit" data-project-id="${project.id}">Chỉnh sửa</button>` : ""}
            ${canManage ? `<button class="btn btn-small btn-danger" type="button" data-action="archive" data-project-id="${project.id}">Lưu trữ</button>` : ""}
          `}
        </span>
      </div>
    </article>`;
  }).join("");
}

function openProjectForm(project = null) {
  editingProjectId = project?.id ?? null;
  projectForm.reset();
  document.getElementById("project-form-title").textContent = project ? "Chỉnh sửa thông tin dự án" : "Khởi tạo dự án mới";
  document.getElementById("project-submit").textContent = project ? "Lưu thay đổi" : "Tạo dự án";
  projectForm.elements.name.value = project?.name || "";
  projectForm.elements.description.value = project?.description || "";
  projectForm.elements.start_date.value = project?.start_date || "";
  projectForm.elements.end_date.value = project?.end_date || "";
  document.getElementById("project-status-label").hidden = !project;
  projectForm.elements.status.hidden = !project;
  if (project) projectForm.elements.status.value = project.status;
  projectDialog.showModal();
  projectForm.elements.name.focus();
}

function renderAdminOverview(summary) {
  document.getElementById("admin-metric-users").textContent = summary.user_count;
  document.getElementById("admin-metric-active-users").textContent = `${summary.active_user_count} đang hoạt động`;
  document.getElementById("admin-metric-projects").textContent = summary.project_count;
  document.getElementById("admin-metric-active-projects").textContent = `${summary.active_project_count} đang hoạt động`;
  document.getElementById("admin-metric-tasks").textContent = summary.task_count;
  document.getElementById("admin-metric-completed-tasks").textContent = `${summary.completed_task_count} đã hoàn thành`;

  const recentUsers = document.getElementById("admin-recent-users");
  recentUsers.innerHTML = summary.recent_users.length ? summary.recent_users.map((user) => `
    <tr>
      <td><strong>${escapeHtml(user.full_name)}</strong><small>@${escapeHtml(user.username)}</small></td>
      <td>${escapeHtml(user.email)}</td>
      <td><span class="role-badge">${escapeHtml(user.system_role)}</span></td>
      <td><span class="role-badge ${user.is_active ? "status-active" : "status-inactive"}">${user.is_active ? "Đang hoạt động" : "Đã khóa"}</span></td>
      <td>${escapeHtml(formatDateTime(user.created_at))}</td>
    </tr>`).join("") : '<tr><td colspan="5" class="muted">Chưa có tài khoản nào.</td></tr>';
}

async function loadDashboard() {
  const token = localStorage.getItem("access_token") || localStorage.getItem("token");
  if (!token) {
    dashboardContent.hidden = true;
    authPrompt.hidden = false;
    return;
  }
  dashboardContent.hidden = false;
  authPrompt.hidden = true;
  projectCards.innerHTML = '<p class="empty-state" style="grid-column: 1 / -1;">Đang tải danh mục dự án…</p>';
  document.getElementById("admin-overview").hidden = true;
  try {
    const user = await api.get("/auth/me");
    const [projectData, metrics, myTasks] = await Promise.all([
      api.get("/projects/summary"),
      api.get("/projects/dashboard/summary"),
      api.get("/tasks/my-tasks", { page: 1, size: 15 }).catch(() => []),
    ]);
    currentUser = user;
    projects = projectData;
    document.getElementById("dashboard-greeting").textContent = `Xin chào, ${user.full_name}`;
    document.getElementById("create-project-button").hidden = false;
    document.getElementById("metric-projects").textContent = metrics.active_project_count;
    document.getElementById("metric-pending").textContent = metrics.pending_task_count;
    document.getElementById("metric-completed").textContent = metrics.completed_task_count;
    const totalMy = (metrics.pending_task_count || 0) + (metrics.completed_task_count || 0);
    const myRate = totalMy ? Math.round((metrics.completed_task_count / totalMy) * 100) : 0;
    const rateEl = document.getElementById("metric-rate");
    if (rateEl) rateEl.textContent = `${myRate}%`;

    renderProjects();
    renderWorkspaceHealth();
    renderUpcomingTasks(myTasks);
    if (typeof renderLayout === "function") {
      renderLayout(projects, user);
    }

    if (user.system_role === "admin") {
      const adminOverview = document.getElementById("admin-overview");
      adminOverview.hidden = false;
      try {
        const summary = await api.get("/admin/users/summary");
        renderAdminOverview(summary);
      } catch (error) {
        document.getElementById("admin-recent-users").innerHTML =
          `<tr><td colspan="5" class="text-error">${escapeHtml(error.message)}</td></tr>`;
        showToast(`Không tải được số liệu quản trị: ${error.message}`, "error");
      }
    }
    window.dispatchEvent(new CustomEvent("layout:user-loaded", { detail: user }));
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      authPrompt.hidden = false;
      dashboardContent.hidden = true;
      return;
    }
    projectCards.innerHTML = `<p class="status status-error" style="grid-column: 1 / -1;">${escapeHtml(error.message)} <button class="btn btn-small" type="button" id="retry-dashboard">Thử lại</button></p>`;
    document.getElementById("retry-dashboard")?.addEventListener("click", loadDashboard);
  }
}

viewGridBtn?.addEventListener("click", () => {
  projectCards.classList.remove("list-mode");
  viewGridBtn.classList.add("active");
  viewListBtn?.classList.remove("active");
});
viewListBtn?.addEventListener("click", () => {
  projectCards.classList.add("list-mode");
  viewListBtn.classList.add("active");
  viewGridBtn?.classList.remove("active");
});

document.getElementById("create-project-button")?.addEventListener("click", () => openProjectForm());
document.getElementById("project-cards")?.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const id = Number(button.dataset.projectId);
  const project = projects.find((item) => item.id === id);
  if (!project) return;
  if (button.dataset.action === "edit") openProjectForm(project);
  if (button.dataset.action === "archive") {
    const ok = await showConfirmModal({
      eyebrow: "LƯU TRỮ DỰ ÁN",
      title: `Lưu trữ "${project.name}"?`,
      message: "Dự án sẽ được chuyển sang trạng thái Đã lưu trữ (chỉ đọc). Bạn vẫn xem lại và khôi phục được bất cứ lúc nào.",
      confirmText: "Lưu trữ dự án",
    });
    if (!ok) return;
    try {
      await api.put(`/projects/${id}`, { status: "archived" });
      showToast("Đã chuyển dự án sang trạng thái Đã lưu trữ");
      await loadDashboard();
    } catch (error) {
      showToast(error.message, "error");
    }
  }
  if (button.dataset.action === "unarchive") {
    try {
      await api.put(`/projects/${id}`, { status: "active" });
      showToast(`Đã khôi phục dự án "${project.name}" sang Đang hoạt động`);
      await loadDashboard();
    } catch (error) {
      showToast(error.message, "error");
    }
  }
  if (button.dataset.action === "delete") {
    const ok = await showConfirmModal({
      eyebrow: "XOÁ DỰ ÁN",
      title: `Xoá dự án "${project.name}"?`,
      message: "Dự án này sẽ bị gỡ khỏi danh sách không gian làm việc của bạn. Bạn có chắc chắn muốn xoá không?",
      confirmText: "Xoá dự án",
      danger: true,
    });
    if (!ok) return;
    try {
      await api.delete(`/projects/${id}`);
      showToast("Đã xoá dự án");
      await loadDashboard();
    } catch (error) {
      showToast(error.message, "error");
    }
  }
});

projectForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(projectForm);
  const payload = {
    name: String(formData.get("name")).trim(),
    description: String(formData.get("description")).trim() || null,
    start_date: formData.get("start_date") || null,
    end_date: formData.get("end_date") || null,
  };
  const submitButton = document.getElementById("project-submit");
  submitButton.disabled = true;
  try {
    if (editingProjectId) {
      payload.status = formData.get("status");
      await api.put(`/projects/${editingProjectId}`, payload);
      showToast("Đã cập nhật dự án");
    } else {
      const created = await api.post("/projects", payload);
      showToast("Đã tạo dự án và ba cột Kanban mặc định");
      projectDialog.close();
      window.location.assign(`pages/project.html?project=${created.id}`);
      return;
    }
    projectDialog.close();
    await loadDashboard();
  } catch (error) {
    if (!applyApiErrorsToForm(projectForm, error)) {
      showToast(error.message, "error");
    }
  } finally {
    submitButton.disabled = false;
  }
});

document.getElementById("project-cards")?.addEventListener("click", (event) => {
  if (event.target.closest("a.project-card-link")) return;
  const button = event.target.closest("button[data-action=edit]");
  if (button) event.preventDefault();
});
projectStatusFilter?.addEventListener("change", renderProjects);
projectSearchInput?.addEventListener("input", renderProjects);
document.getElementById("global-search-input")?.addEventListener("input", (e) => {
  if (projectSearchInput) {
    projectSearchInput.value = e.target.value;
    renderProjects();
  }
});
document.querySelectorAll("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => projectDialog.close()));
projectDialog?.addEventListener("click", (event) => {
  if (event.target === projectDialog) projectDialog.close();
});
window.addEventListener("hashchange", () => {
  if (window.location.hash === "#new-project" && dashboardContent && !dashboardContent.hidden) openProjectForm();
});

if (dashboardContent) {
  loadDashboard();
}
