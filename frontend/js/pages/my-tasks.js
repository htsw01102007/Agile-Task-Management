const taskFilters = document.getElementById("task-filters");
const taskList = document.getElementById("my-task-list");
const taskPageLabel = document.getElementById("task-page");
const taskPageSize = 50;
const taskPriorityNames = { low: "Thấp", medium: "Trung bình", high: "Cao", urgent: "Khẩn" };
let taskPage = 1;
let tasks = [];
let projectMap = new Map();
let listMap = new Map();

async function loadMyTasks() {
  taskList.innerHTML = '<p class="muted">Đang tải công việc…</p>';
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
    const listResults = await Promise.all(projects.map(async (project) => [project.id, await api.get(`/projects/${project.id}/lists`)]));
    listMap = new Map(listResults.flatMap(([id, lists]) => lists.map((list) => [`${id}:${list.id}`, list])));
    taskList.innerHTML = tasks.length ? tasks.map((task) => {
      const project = projectMap.get(task.project_id);
      const list = listMap.get(`${task.project_id}:${task.list_id}`);
      const completed = Boolean(task.completed_at) || Boolean(list?.is_done_column);
      const due = task.due_date ? new Date(task.due_date) : null;
      const overdue = due && due.getTime() < Date.now() && !completed;
      return `<a class="my-task-row" href="project.html?project=${task.project_id}&task=${task.id}">
        <span class="task-status-dot ${completed ? "done" : ""}"></span><span class="my-task-main"><strong>${escapeHtml(task.title)}</strong><small>${escapeHtml(project?.name || `Dự án #${task.project_id}`)} · ${escapeHtml(list?.name || `Cột #${task.list_id}`)}</small></span>
        <span class="priority priority-${escapeHtml(task.priority)}">${escapeHtml(taskPriorityNames[task.priority] || task.priority)}</span>
        <span class="my-task-due ${overdue ? "overdue" : ""}">${due ? escapeHtml(formatDateTime(task.due_date)) : "Chưa đặt hạn"}</span>
      </a>`;
    }).join("") : '<p class="empty-state">Không có công việc nào phù hợp.</p>';
    taskPageLabel.textContent = `Trang ${taskPage}`;
    document.getElementById("task-prev").disabled = taskPage <= 1;
    document.getElementById("task-next").disabled = tasks.length < taskPageSize;
  } catch (error) {
    taskList.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}

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
    result.textContent = `Backend kết nối được; MySQL: ${health.database}. API: ${CONFIG.API_BASE_URL}`;
    result.className = "status status-ok";
  } catch (error) {
    result.textContent = `${error.message} API: ${CONFIG.API_BASE_URL}`;
    result.className = "status status-error";
  } finally {
    button.disabled = false;
  }
});

loadMyTasks();
