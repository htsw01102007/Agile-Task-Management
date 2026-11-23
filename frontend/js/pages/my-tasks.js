const taskFilters = document.getElementById("task-filters");
const taskList = document.getElementById("my-task-list");
const taskPageLabel = document.getElementById("task-page");
const projectSelect = document.getElementById("my-project-filter");
const taskPageSize = 50;
const taskPriorityNames = { low: "Thấp", medium: "Trung bình", high: "Cao", urgent: "Khẩn cấp" };
let taskPage = 1;
let tasks = [];
let projectMap = new Map();
let listMap = new Map();

function renderMyTasksList() {
  const selectedProjId = projectSelect?.value || "";
  const visible = selectedProjId
    ? tasks.filter((t) => String(t.project_id) === selectedProjId)
    : tasks;

  let doneCount = 0;
  let overdueCount = 0;

  visible.forEach((task) => {
    const list = listMap.get(`${task.project_id}:${task.list_id}`);
    const completed = Boolean(task.completed_at) || Boolean(list?.is_done_column);
    const due = task.due_date ? new Date(task.due_date) : null;
    const overdue = due && due.getTime() < Date.now() && !completed;
    if (completed) doneCount += 1;
    if (overdue) overdueCount += 1;
  });

  const statTotal = document.getElementById("my-stat-total");
  const statPending = document.getElementById("my-stat-pending");
  const statDone = document.getElementById("my-stat-done");
  const statOverdue = document.getElementById("my-stat-overdue");
  if (statTotal) statTotal.textContent = visible.length;
  if (statPending) statPending.textContent = Math.max(0, visible.length - doneCount);
  if (statDone) statDone.textContent = doneCount;
  if (statOverdue) statOverdue.textContent = overdueCount;

  taskList.innerHTML = visible.length ? visible.map((task) => {
    const project = projectMap.get(task.project_id);
    const list = listMap.get(`${task.project_id}:${task.list_id}`);
    const completed = Boolean(task.completed_at) || Boolean(list?.is_done_column);
    const due = task.due_date ? new Date(task.due_date) : null;
    const overdue = due && due.getTime() < Date.now() && !completed;
    return `<a class="my-task-row" href="project.html?project=${task.project_id}&task=${task.id}">
      <span class="task-status-dot ${completed ? "done" : ""}"></span>
      <span class="task-id-badge">#${task.id}</span>
      <span class="my-task-main">
        <strong style="${completed ? "text-decoration:line-through;color:var(--muted);" : ""}">${escapeHtml(task.title)}</strong>
        <small>Dự án: <b>${escapeHtml(project?.name || `#${task.project_id}`)}</b> · Cột: ${escapeHtml(list?.name || `#${task.list_id}`)}</small>
      </span>
      <span class="role-badge ${completed ? "status-active" : ""}">${escapeHtml(list?.name || "Kanban")}</span>
      <span class="priority priority-${escapeHtml(task.priority)}">↑ ${escapeHtml(taskPriorityNames[task.priority] || task.priority)}</span>
      <span class="my-task-due ${overdue ? "overdue" : ""}">${due ? `${overdue ? "! Quá hạn " : "◷ "}${escapeHtml(formatDateTime(task.due_date))}` : "Chưa đặt hạn"}</span>
    </a>`;
  }).join("") : '<p class="empty-state">Không tìm thấy công việc nào khớp với tiêu chí lọc.</p>';
}

async function loadMyTasks() {
  taskList.innerHTML = '<p class="empty-state">Đang tải danh sách công việc…</p>';
  const form = new FormData(taskFilters);
  const params = { page: taskPage, size: taskPageSize };
  for (const key of ["search", "priority", "is_completed", "is_overdue"]) {
    const value = String(form.get(key) || "").trim();
    if (value) params[key] = value;
  }
  try {
    const [result, projects] = await Promise.all([api.get("/tasks/my-tasks", params), api.get("/projects/summary")]);
    tasks = result;
    projectMap = new Map(projects.map((project) => [project.id, project]));

    if (projectSelect) {
      const currentProj = projectSelect.value;
      projectSelect.innerHTML = '<option value="">Tất cả dự án</option>' + projects.map((p) => `<option value="${p.id}" ${String(p.id) === currentProj ? "selected" : ""}>${escapeHtml(p.name)}</option>`).join("");
    }

    const listResults = await Promise.all(projects.map(async (project) => [project.id, await api.get(`/projects/${project.id}/lists`)]));
    listMap = new Map(listResults.flatMap(([id, lists]) => lists.map((list) => [`${id}:${list.id}`, list])));

    renderMyTasksList();

    taskPageLabel.textContent = `Trang ${taskPage}`;
    document.getElementById("task-prev").disabled = taskPage <= 1;
    document.getElementById("task-next").disabled = tasks.length < taskPageSize;
  } catch (error) {
    taskList.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}

document.getElementById("quick-task-tabs")?.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-quick-filter]");
  if (!btn) return;
  document.querySelectorAll("#quick-task-tabs .pill-tab").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  const mode = btn.dataset.quickFilter;
  taskFilters.elements.is_completed.value = mode === "done" ? "true" : mode === "pending" || mode === "overdue" ? "false" : "";
  taskFilters.elements.is_overdue.value = mode === "overdue" ? "true" : "";
  taskPage = 1;
  loadMyTasks();
});

projectSelect?.addEventListener("change", renderMyTasksList);
taskFilters.addEventListener("submit", (event) => { event.preventDefault(); taskPage = 1; loadMyTasks(); });
document.getElementById("task-prev").addEventListener("click", () => { if (taskPage > 1) { taskPage -= 1; loadMyTasks(); } });
document.getElementById("task-next").addEventListener("click", () => { if (tasks.length === taskPageSize) { taskPage += 1; loadMyTasks(); } });
document.getElementById("check-backend").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const result = document.getElementById("backend-health-result");
  button.disabled = true;
  result.hidden = false;
  result.textContent = `Đang kiểm tra ${CONFIG.API_BASE_URL}/health…`;
  try {
    const health = await api.health();
    result.textContent = `✓ Kết nối Backend ổn định · MySQL: ${health.database} · Endpoint: ${CONFIG.API_BASE_URL}`;
    result.className = "status status-ok";
  } catch (error) {
    result.textContent = `${error.message} API: ${CONFIG.API_BASE_URL}`;
    result.className = "status status-error";
  } finally {
    button.disabled = false;
  }
});

loadMyTasks();
