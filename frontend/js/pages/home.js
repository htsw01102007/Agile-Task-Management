const dashboardDate = document.getElementById("dashboard-date");
const dashboardContent = document.getElementById("dashboard-content");
const authPrompt = document.getElementById("dashboard-auth-prompt");
const projectCards = document.getElementById("project-cards");
const projectDialog = document.getElementById("project-dialog");
const projectForm = document.getElementById("project-form");
const projectStatusFilter = document.getElementById("project-status-filter");

let projects = [];
let currentUser = null;
let editingProjectId = null;

if (dashboardDate) {
  dashboardDate.textContent = new Intl.DateTimeFormat("vi-VN", {
    weekday: "long",
    day: "numeric",
    month: "numeric",
  }).format(new Date()).toUpperCase();
}

function projectStatusText(status) {
  return { active: "Đang hoạt động", completed: "Hoàn thành", archived: "Đã lưu trữ" }[status] || status;
}

function renderProjects() {
  const statusFilter = projectStatusFilter.value;
  const visibleProjects = projects.filter((project) => !statusFilter || project.status === statusFilter);
  if (!visibleProjects.length) {
    projectCards.innerHTML = `<p class="empty-state">${projects.length ? "Không có dự án phù hợp bộ lọc." : "Bạn chưa tham gia dự án nào."}${projects.length ? "" : '<br><span>Tạo dự án mới để bắt đầu.</span>'}</p>`;
    return;
  }
  projectCards.innerHTML = visibleProjects.map((project, index) => {
    const canManage = ["owner", "manager"].includes(project.user_role);
    const canDelete = project.user_role === "owner";
    const canEdit = canManage && project.status === "active";
    const color = ["teal", "amber", "violet"][index % 3];
    return `<article class="project-card project-entry">
      <a class="project-card-link" href="pages/project.html?project=${project.id}">
        <div class="project-card-top"><span class="project-mark ${color}">${escapeHtml(layoutInitials(project.name))}</span><span class="project-status"><i class="${project.status === "active" ? "" : "status-inactive"}"></i>${escapeHtml(projectStatusText(project.status))}</span></div>
        <h3>${escapeHtml(project.name)}</h3><p class="muted">${escapeHtml(project.description || "Chưa có mô tả.")}</p>
        <div class="project-progress"><div><span>Tiến độ · ${project.task_count} việc</span><strong>${Math.round(project.completion_rate)}%</strong></div><progress value="${project.completion_rate}" max="100"></progress></div>
      </a>
      <div class="project-card-bottom"><span>♙ ${project.member_count} thành viên · ${escapeHtml(project.user_role || "")}</span><span class="project-card-actions">
        ${canManage ? `<button class="btn btn-small" type="button" data-action="edit" data-project-id="${project.id}" ${canEdit ? "" : "disabled"}>Sửa</button>` : ""}
        ${canDelete ? `<button class="btn btn-small btn-danger" type="button" data-action="delete" data-project-id="${project.id}">Xoá</button>` : ""}
      </span></div>
    </article>`;
  }).join("");
}

function openProjectForm(project = null) {
  editingProjectId = project?.id ?? null;
  projectForm.reset();
  document.getElementById("project-form-title").textContent = project ? "Chỉnh sửa dự án" : "Tạo dự án";
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
      <td>${escapeHtml(user.system_role)}</td>
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
  projectCards.innerHTML = '<p class="empty-state">Đang tải dự án…</p>';
  document.getElementById("admin-overview").hidden = true;
  try {
    const user = await api.get("/auth/me");
    const [projectData, metrics] = await Promise.all([
      api.get("/projects/summary"),
      api.get("/projects/dashboard/summary"),
    ]);
    currentUser = user;
    projects = projectData;
    document.getElementById("dashboard-greeting").textContent = `Chào ${user.full_name}`;
    document.getElementById("create-project-button").hidden = false;
    document.getElementById("metric-projects").textContent = metrics.active_project_count;
    document.getElementById("metric-pending").textContent = metrics.pending_task_count;
    document.getElementById("metric-completed").textContent = metrics.completed_task_count;
    renderProjects();
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
    projectCards.innerHTML = `<p class="status status-error">${escapeHtml(error.message)} <button class="btn btn-small" type="button" id="retry-dashboard">Thử lại</button></p>`;
    document.getElementById("retry-dashboard").addEventListener("click", loadDashboard);
  }
}

document.getElementById("create-project-button").addEventListener("click", () => openProjectForm());
document.getElementById("project-cards").addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const id = Number(button.dataset.projectId);
  const project = projects.find((item) => item.id === id);
  if (!project) return;
  if (button.dataset.action === "edit") openProjectForm(project);
  if (button.dataset.action === "delete" && confirm(`Xoá mềm dự án "${project.name}"?`)) {
    try {
      await api.delete(`/projects/${id}`);
      showToast("Đã chuyển dự án vào lưu trữ");
      await loadDashboard();
    } catch (error) {
      showToast(error.message, "error");
    }
  }
});

projectForm.addEventListener("submit", async (event) => {
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
    showToast(error.message, "error");
  } finally {
    submitButton.disabled = false;
  }
});

document.getElementById("project-cards").addEventListener("click", (event) => {
  if (event.target.closest("a.project-card-link")) return;
  const button = event.target.closest("button[data-action=edit]");
  if (button) event.preventDefault();
});
projectStatusFilter.addEventListener("change", renderProjects);
document.querySelectorAll("[data-close-dialog]").forEach((button) => button.addEventListener("click", () => projectDialog.close()));
projectDialog.addEventListener("click", (event) => {
  if (event.target === projectDialog) projectDialog.close();
});
window.addEventListener("hashchange", () => {
  if (window.location.hash === "#new-project" && !dashboardContent.hidden) openProjectForm();
});

loadDashboard();
