const boardElement = document.getElementById("board");
const summaryElement = document.getElementById("board-summary");
const retryButton = document.getElementById("retry-board");
const newTaskButton = document.getElementById("new-task-button");
const teamButton = document.getElementById("team-button");
const searchInput = document.getElementById("task-search");
const priorityFilter = document.getElementById("priority-filter");
const taskDialog = document.getElementById("task-dialog");
const taskForm = document.getElementById("task-form");
const teamDialog = document.getElementById("team-dialog");
const trashDialog = document.getElementById("trash-dialog");
const priorityNames = { low: "Thấp", medium: "Trung bình", high: "Cao", urgent: "Khẩn" };

const requestedProjectId = new URLSearchParams(window.location.search).get("project");
let projectId = /^\d+$/.test(requestedProjectId || "") ? Number(requestedProjectId) : NaN;
let projectData = null;
let boardData = null;
let currentUser = null;
let members = [];
let currentTask = null;
let savingTask = false;
let canEdit = false;
let canManageLists = false;

function initials(name = "?") {
  return name.trim().split(/\s+/).slice(-2).map((part) => part[0]).join("").toUpperCase();
}

function statusText(status) {
  return { active: "Đang hoạt động", completed: "Đã hoàn thành", archived: "Đã lưu trữ" }[status] || status;
}

function priorityText(priority) {
  return priorityNames[priority] || priority;
}

function isTaskDone(task) {
  return Boolean(task.completed_at) || boardData.lists.some((list) => list.id === task.list_id && list.is_done_column);
}

function formatDueDate(value, completed) {
  if (!value) return { text: "Chưa đặt hạn", overdue: false };
  const due = new Date(value);
  if (Number.isNaN(due.getTime())) return { text: "Hạn chót không hợp lệ", overdue: false };
  const formatted = new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  }).format(due);
  const overdue = !completed && due.getTime() < Date.now();
  return {
    text: completed ? `✓ Hoàn thành ${formatted}` : overdue ? `! Quá hạn ${formatted}` : `◷ ${formatted}`,
    overdue,
  };
}

function toDateTimeInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

function toUtcTimestamp(value) {
  return value ? new Date(value).toISOString() : null;
}

function assigneeMarkup(assignees = []) {
  if (!assignees.length) return '<span class="task-unassigned">Chưa giao</span>';
  const shown = assignees.slice(0, 3).map((person) => {
    const name = person.user_full_name || person.user_email || "Người thực hiện";
    const safeName = escapeHtml(name);
    return person.user_avatar_url
      ? `<img class="task-avatar" src="${escapeHtml(person.user_avatar_url)}" alt="${safeName}" title="${safeName}">`
      : `<span class="task-avatar task-avatar-fallback" title="${safeName}">${escapeHtml(initials(name))}</span>`;
  }).join("");
  const remainder = assignees.length > 3 ? `<span class="task-avatar task-avatar-more">+${assignees.length - 3}</span>` : "";
  return `<span class="task-assignees" aria-label="Người thực hiện">${shown}${remainder}</span>`;
}

function taskMarkup(task) {
  const completed = isTaskDone(task);
  const due = formatDueDate(task.due_date, completed);
  const priority = priorityNames[task.priority] ? task.priority : "medium";
  return `<article class="task-card${completed ? " completed-task" : ""}" tabindex="0" draggable="${canEdit}" data-task-id="${task.id}">
    <h3>${escapeHtml(task.title)}</h3>
    <div class="task-card-meta"><span class="priority priority-${priority}">↑ ${escapeHtml(priorityText(task.priority))}</span><span class="task-date${due.overdue ? " overdue" : ""}">${due.text}</span></div>
    <div class="task-footer">${assigneeMarkup(task.assignees)}</div>
  </article>`;
}

function renderInsights() {
  const completed = boardData.tasks.filter(isTaskDone).length;
  const overdue = boardData.tasks.filter((task) => !isTaskDone(task) && task.due_date && new Date(task.due_date).getTime() < Date.now()).length;
  document.getElementById("stat-total").textContent = boardData.tasks.length;
  document.getElementById("stat-active").textContent = boardData.tasks.length - completed;
  document.getElementById("stat-completed").textContent = completed;
  document.getElementById("stat-overdue").textContent = overdue;
  const rate = boardData.tasks.length ? Math.round(completed / boardData.tasks.length * 100) : 0;
  document.getElementById("project-progress-label").textContent = `${rate}% hoàn thành`;
  document.getElementById("project-progress").value = rate;
  document.getElementById("project-counts").textContent = `${completed}/${boardData.tasks.length} công việc`;
}

function renderBoard() {
  if (!boardData) return;
  const query = searchInput.value.trim().toLocaleLowerCase("vi");
  const selectedPriority = priorityFilter.value;
  const visibleTasks = boardData.tasks.filter((task) => {
    return (!query || task.title.toLocaleLowerCase("vi").includes(query))
      && (!selectedPriority || task.priority === selectedPriority);
  });
  const columns = [...boardData.lists].sort((a, b) => a.position - b.position || a.id - b.id);
  boardElement.innerHTML = columns.map((list) => {
    const tasks = visibleTasks.filter((task) => task.list_id === list.id)
      .sort((a, b) => a.position - b.position || a.id - b.id);
    const content = tasks.length ? tasks.map(taskMarkup).join("")
      : `<p class="board-empty">${visibleTasks.length ? "Chưa có công việc" : "Không có kết quả phù hợp"}</p>`;
    const listActions = canManageLists ? `<span class="column-actions">
      <button type="button" class="column-action" data-list-action="rename" data-list-id="${list.id}" aria-label="Đổi tên cột">✎</button>
      <button type="button" class="column-action" data-list-action="done" data-list-id="${list.id}" aria-label="Đặt cột hoàn thành">${list.is_done_column ? "✓" : "○"}</button>
      <button type="button" class="column-action" data-list-action="delete" data-list-id="${list.id}" aria-label="Xoá cột">⋯</button>
    </span>` : "";
    const addTask = canEdit ? `<button type="button" class="add-task" data-create-task="${list.id}">＋ Thêm công việc</button>` : "";
    return `<section class="board-column${list.is_done_column ? " board-column-done" : ""}" data-list-id="${list.id}" aria-label="${escapeHtml(list.name)}" draggable="${canManageLists}">
      <div class="column-title" ${canManageLists ? 'data-list-drag-handle="true"' : ""}><span class="column-dot${list.is_done_column ? " done-dot" : ""}"></span><strong>${escapeHtml(list.name)}</strong><span class="count">${tasks.length}</span>${listActions}</div>
      <div class="column-tasks">${content}</div>${addTask}
    </section>`;
  }).join("") + (canManageLists ? '<button type="button" id="add-list-button" class="add-list">＋ Thêm danh sách</button>' : "");
  const completedCount = boardData.tasks.filter(isTaskDone).length;
  summaryElement.textContent = `${boardData.lists.length} cột · ${visibleTasks.length} công việc${visibleTasks.length !== boardData.tasks.length ? ` (lọc từ ${boardData.tasks.length})` : ""} · Hoàn thành ${boardData.tasks.length ? Math.round(completedCount / boardData.tasks.length * 100) : 0}%`;
  renderInsights();
}

function renderProject() {
  document.title = `${projectData.name} | Agile Workspace`;
  document.getElementById("project-title").textContent = projectData.name;
  document.getElementById("project-crumb").textContent = projectData.name;
  document.getElementById("project-description").textContent = projectData.description || "";
  document.getElementById("project-mark").textContent = initials(projectData.name);
  document.getElementById("project-status").textContent = statusText(projectData.status);
  const active = projectData.status === "active";
  canEdit = active && ["owner", "manager", "member"].includes(projectData.user_role);
  canManageLists = active && ["owner", "manager"].includes(projectData.user_role);
  document.getElementById("readonly-banner").hidden = active;
  newTaskButton.hidden = !canEdit;
  teamButton.hidden = !["owner", "manager"].includes(projectData.user_role);
  document.getElementById("trash-button").hidden = !active || !["owner", "manager"].includes(projectData.user_role);
}

function renderLoading() {
  boardData = null;
  boardElement.innerHTML = Array.from({ length: 3 }, () => '<section class="board-column board-skeleton"><span></span><span></span><span></span></section>').join("");
  boardElement.setAttribute("aria-busy", "true");
  retryButton.hidden = true;
}

async function resolveProjectId() {
  if (Number.isSafeInteger(projectId) && projectId > 0) return projectId;
  const projects = await api.get("/projects/summary");
  if (!projects.length) throw new Error("Bạn chưa có dự án. Hãy tạo một dự án từ trang Tổng quan.");
  projectId = projects[0].id;
  const url = new URL(window.location.href);
  url.searchParams.set("project", projectId);
  window.history.replaceState({}, "", url);
  return projectId;
}

async function loadBoard() {
  renderLoading();
  try {
    const id = await resolveProjectId();
    const [project, board, user] = await Promise.all([
      api.get(`/projects/${id}`),
      api.get(`/projects/${id}/board`),
      api.get("/auth/me"),
    ]);
    projectData = project;
    boardData = board;
    currentUser = user;
    renderProject();
    renderBoard();
    if (window.location.hash === "#activity") setProjectTab("activity");
    boardElement.setAttribute("aria-busy", "false");
    const taskId = Number(new URLSearchParams(window.location.search).get("task"));
    if (Number.isSafeInteger(taskId) && taskId > 0 && !taskDialog.open) await openTask(taskId, false);
  } catch (error) {
    boardElement.setAttribute("aria-busy", "false");
    const loginLink = error.status === 401
      ? `<a href="../pages/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}">Đăng nhập để xem bảng dự án</a>`
      : '<a href="../index.html">Về danh sách dự án</a>';
    boardElement.innerHTML = `<div class="board-load-error"><strong>Không tải được bảng công việc.</strong><span>${escapeHtml(error.message)}</span>${loginLink}</div>`;
    summaryElement.textContent = "Đã xảy ra lỗi khi tải dữ liệu.";
    retryButton.hidden = false;
    if (error.status === 401) window.location.assign(`../pages/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
  }
}

function buildTaskPayload() {
  return {
    title: taskForm.elements.title.value.trim(),
    description: taskForm.elements.description.value.trim() || null,
    list_id: Number(taskForm.elements.list_id.value),
    priority: taskForm.elements.priority.value,
    start_date: toUtcTimestamp(taskForm.elements.start_date.value),
    due_date: toUtcTimestamp(taskForm.elements.due_date.value),
  };
}

function selectedAssigneeIds() {
  return Array.from(taskForm.elements.assignee_ids.selectedOptions).map((option) => Number(option.value));
}

function populateTaskLists(selectedId) {
  taskForm.elements.list_id.innerHTML = boardData.lists
    .map((list) => `<option value="${list.id}" ${list.id === selectedId ? "selected" : ""}>${escapeHtml(list.name)}</option>`)
    .join("");
}

function populateAssignees(selectedIds = []) {
  taskForm.elements.assignee_ids.innerHTML = members
    .filter((member) => member.role !== "viewer" && member.user?.is_active !== false)
    .map((member) => `<option value="${member.user_id}" ${selectedIds.includes(member.user_id) ? "selected" : ""}>${escapeHtml(member.user?.full_name || member.user?.email || `Thành viên #${member.user_id}`)}</option>`)
    .join("");
}

function setTaskFormReadOnly(readOnly) {
  taskForm.querySelectorAll("input, textarea, select").forEach((input) => { input.disabled = readOnly; });
  document.getElementById("task-submit").hidden = readOnly;
}

function openTaskForm(listId, task = null) {
  currentTask = task;
  taskForm.reset();
  document.getElementById("task-dialog-title").textContent = task ? task.title : "Tạo công việc";
  document.getElementById("task-dialog-context").textContent = task ? `CÔNG VIỆC #${task.id}` : "CÔNG VIỆC MỚI";
  document.getElementById("task-submit").textContent = task ? "Lưu thay đổi" : "Tạo công việc";
  document.getElementById("task-delete").hidden = !task || !canDeleteTask(task);
  document.getElementById("task-completed-at").textContent = task?.completed_at ? `Hoàn thành: ${formatDueDate(task.completed_at, true).text}` : "";
  document.getElementById("task-created-by").textContent = task ? `Người tạo: ${task.creator_name || `#${task.created_by}`}` : "";
  taskForm.elements.title.value = task?.title || "";
  taskForm.elements.description.value = task?.description || "";
  taskForm.elements.priority.value = task?.priority || "medium";
  taskForm.elements.start_date.value = toDateTimeInput(task?.start_date);
  taskForm.elements.due_date.value = toDateTimeInput(task?.due_date);
  populateTaskLists(task?.list_id || listId || boardData.lists[0]?.id);
  populateAssignees((task?.assignees || []).map((assignee) => assignee.user_id));
  ["checklist-panel", "comments-panel", "attachments-panel"].forEach((id) => { document.getElementById(id).hidden = !task; });
  setTaskFormReadOnly(!canEdit);
  taskDialog.showModal();
  if (task) {
    loadTaskExtras(task.id);
  } else {
    taskForm.elements.title.focus();
  }
}

function canDeleteTask(task) {
  return projectData.status === "active"
    && (["owner", "manager"].includes(projectData.user_role)
      || (projectData.user_role === "member" && task.created_by === currentUser.id));
}

async function openTask(taskId, updateUrl = true) {
  try {
    const task = await api.get(`/projects/${projectId}/tasks/${taskId}`);
    const memberPromise = members.length ? Promise.resolve(members) : api.get(`/projects/${projectId}/members`);
    members = await memberPromise;
    currentTask = task;
    if (updateUrl) {
      const url = new URL(window.location.href);
      url.searchParams.set("task", taskId);
      window.history.pushState({ taskId }, "", url);
    }
    openTaskForm(task.list_id, task);
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function syncAssignees(taskId, selectedIds) {
  const currentIds = new Set((currentTask?.assignees || []).map((assignee) => assignee.user_id));
  const desiredIds = new Set(selectedIds);
  const addIds = [...desiredIds].filter((id) => !currentIds.has(id));
  const removeIds = [...currentIds].filter((id) => !desiredIds.has(id));
  if (addIds.length) await api.post(`/projects/${projectId}/tasks/${taskId}/assignees`, { user_ids: addIds });
  for (const id of removeIds) await api.delete(`/projects/${projectId}/tasks/${taskId}/assignees/${id}`);
}

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (savingTask || !canEdit) return;
  const submitButton = document.getElementById("task-submit");
  savingTask = true;
  submitButton.disabled = true;
  try {
    const payload = buildTaskPayload();
    if (payload.start_date && payload.due_date && new Date(payload.due_date) < new Date(payload.start_date)) {
      showToast("Hạn chót không được sớm hơn ngày bắt đầu", "error");
      return;
    }
    if (currentTask) {
      const taskId = currentTask.id;
      const assigneeIds = selectedAssigneeIds();
      await api.put(`/projects/${projectId}/tasks/${taskId}`, payload);
      try {
        await syncAssignees(taskId, assigneeIds);
      } catch (error) {
        showToast(`Đã lưu công việc nhưng chưa cập nhật người thực hiện: ${error.message}`, "error");
        await openTask(taskId, false);
        await loadBoard();
        return;
      }
      showToast("Đã cập nhật công việc");
      closeTaskDialog();
      await loadBoard();
    } else {
      payload.assignee_ids = selectedAssigneeIds();
      const created = await api.post(`/projects/${projectId}/tasks`, payload);
      showToast("Đã tạo công việc");
      closeTaskDialog();
      await loadBoard();
      await openTask(created.id);
    }
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    savingTask = false;
    submitButton.disabled = false;
  }
});

function closeTaskDialog() {
  if (taskDialog.open) taskDialog.close();
}

taskDialog.addEventListener("close", () => {
  currentTask = null;
  const url = new URL(window.location.href);
  if (url.searchParams.has("task")) {
    url.searchParams.delete("task");
    window.history.replaceState({}, "", url);
  }
});
taskDialog.querySelectorAll("[data-close-task]").forEach((button) => button.addEventListener("click", closeTaskDialog));
taskDialog.addEventListener("click", (event) => {
  if (event.target === taskDialog) closeTaskDialog();
});
window.addEventListener("popstate", () => {
  const taskId = Number(new URLSearchParams(window.location.search).get("task"));
  if (taskId && !taskDialog.open) openTask(taskId, false);
  else if (!taskId && taskDialog.open) closeTaskDialog();
});

document.getElementById("task-delete").addEventListener("click", async () => {
  if (!currentTask || !canDeleteTask(currentTask)) return;
  if (!confirm(`Xoá công việc "${currentTask.title}"? Công việc sẽ được chuyển vào thùng rác.`)) return;
  try {
    await api.delete(`/projects/${projectId}/tasks/${currentTask.id}`);
    showToast("Đã xoá công việc");
    closeTaskDialog();
    await loadBoard();
  } catch (error) {
    showToast(error.message, "error");
  }
});

async function loadDeletedTasks() {
  const container = document.getElementById("deleted-tasks");
  container.innerHTML = '<p class="muted">Đang tải công việc đã xoá…</p>';
  try {
    const deleted = await api.get(`/projects/${projectId}/tasks/deleted`);
    container.innerHTML = deleted.length ? deleted.map((task) => `
      <div class="team-row"><span class="team-person"><strong>${escapeHtml(task.title)}</strong><small>Đã xoá ${escapeHtml(task.deleted_at ? formatDateTime(task.deleted_at) : "")}</small></span><button class="btn btn-small" type="button" data-restore-task="${task.id}">Khôi phục</button></div>`).join("")
      : '<p class="muted">Thùng rác đang trống.</p>';
  } catch (error) {
    container.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}
document.getElementById("trash-button").addEventListener("click", async () => {
  if (!trashDialog.open) trashDialog.showModal();
  await loadDeletedTasks();
});
document.querySelectorAll("[data-close-trash]").forEach((button) => button.addEventListener("click", () => trashDialog.close()));
trashDialog.addEventListener("click", (event) => {
  if (event.target === trashDialog) trashDialog.close();
});
document.getElementById("deleted-tasks").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-restore-task]");
  if (!button) return;
  try {
    await api.post(`/projects/${projectId}/tasks/${button.dataset.restoreTask}/restore`);
    showToast("Đã khôi phục công việc");
    await loadBoard();
    await loadDeletedTasks();
  } catch (error) {
    showToast(error.message, "error");
  }
});

async function loadTaskExtras(taskId) {
  try {
    const [checklist, comments, attachments] = await Promise.all([
      api.get(`/projects/${projectId}/tasks/${taskId}/checklist/summary`),
      api.get(`/projects/${projectId}/tasks/${taskId}/comments`),
      api.get(`/projects/${projectId}/tasks/${taskId}/attachments`),
    ]);
    if (!currentTask || currentTask.id !== taskId) return;
    renderChecklist(checklist);
    renderComments(comments);
    renderAttachments(attachments);
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderChecklist(summary) {
  const completedCount = summary.completed_items || 0;
  const totalCount = summary.total_items || 0;
  document.getElementById("checklist-progress").textContent = `${completedCount}/${totalCount} · ${Math.round(summary.progress_percent || 0)}%`;
  document.getElementById("checklist-items").innerHTML = summary.items.length ? summary.items.map((item) => `
    <div class="checklist-item" data-checklist-id="${item.id}">
      <input type="checkbox" ${item.is_done ? "checked" : ""} ${canEdit ? "" : "disabled"}>
      <span>${escapeHtml(item.content)}</span>
      ${canEdit ? `<button type="button" class="column-action" data-checklist-delete="${item.id}" aria-label="Xoá mục">×</button>` : ""}
    </div>`).join("") : '<p class="muted">Chưa có mục checklist.</p>';
  document.getElementById("checklist-form").hidden = !canEdit;
}

function renderComments(comments) {
  document.getElementById("task-comments").innerHTML = comments.length ? comments.map((comment) => `
    <article class="task-comment"><span class="comment-avatar">${escapeHtml(initials(comment.user_full_name || "Người dùng"))}</span><div><strong>${escapeHtml(comment.user_full_name || "Tài khoản")}</strong><time>${escapeHtml(formatDateTime(comment.created_at))}</time><p>${escapeHtml(comment.content)}</p></div></article>`).join("") : '<p class="muted">Chưa có bình luận.</p>';
  document.getElementById("comment-form").hidden = !canEdit;
}

function renderAttachments(attachments) {
  document.getElementById("task-attachments").innerHTML = attachments.length ? attachments.map((attachment) => `
    <div class="attachment-row"><span>▤</span><span class="team-person"><strong>${escapeHtml(attachment.file_name)}</strong><small>${(attachment.file_size / 1024).toFixed(1)} KB · ${escapeHtml(attachment.user_full_name || attachment.user_email || "Tài khoản")}</small></span>
      <button class="btn btn-small" type="button" data-download-attachment="${attachment.id}">Tải xuống</button>
      ${canEdit && (attachment.user_id === currentUser.id || ["owner", "manager"].includes(projectData.user_role)) ? `<button class="btn btn-small btn-danger" type="button" data-delete-attachment="${attachment.id}">Xoá</button>` : ""}
    </div>`).join("") : '<p class="muted">Chưa có tệp đính kèm.</p>';
  document.getElementById("attachment-upload-label").hidden = !canEdit;
}

document.getElementById("attachment-upload").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file || !currentTask) return;
  if (file.size > 10 * 1024 * 1024) {
    showToast("Tệp vượt quá giới hạn 10 MB.", "error");
    event.target.value = "";
    return;
  }
  const body = new FormData();
  body.append("file", file);
  try {
    await http.post(`/projects/${projectId}/tasks/${currentTask.id}/attachments`, body, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    showToast("Đã tải tệp lên");
    renderAttachments(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/attachments`));
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    event.target.value = "";
  }
});

document.getElementById("task-attachments").addEventListener("click", async (event) => {
  const download = event.target.closest("[data-download-attachment]");
  const remove = event.target.closest("[data-delete-attachment]");
  if (!download && !remove) return;
  if (!currentTask) return;
  try {
    if (remove) {
      if (!confirm("Xoá tệp đính kèm này?")) return;
      await api.delete(`/projects/${projectId}/tasks/${currentTask.id}/attachments/${remove.dataset.deleteAttachment}`);
      showToast("Đã xoá tệp đính kèm");
      renderAttachments(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/attachments`));
      return;
    }
    const response = await http.get(`/projects/${projectId}/tasks/${currentTask.id}/attachments/${download.dataset.downloadAttachment}/download`, { responseType: "blob" });
    const attachment = (await api.get(`/projects/${projectId}/tasks/${currentTask.id}/attachments`))
      .find((item) => item.id === Number(download.dataset.downloadAttachment));
    const objectUrl = URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = attachment?.file_name || "attachment";
    link.click();
    URL.revokeObjectURL(objectUrl);
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.getElementById("checklist-form").querySelector("button").addEventListener("click", async () => {
  const input = document.getElementById("checklist-form").querySelector('[name="content"]');
  const content = input.value.trim();
  if (!content || !currentTask) return;
  try {
    await api.post(`/projects/${projectId}/tasks/${currentTask.id}/checklist`, { content });
    input.value = "";
    const data = await api.get(`/projects/${projectId}/tasks/${currentTask.id}/checklist/summary`);
    renderChecklist(data);
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.getElementById("checklist-items").addEventListener("change", async (event) => {
  const item = event.target.closest("[data-checklist-id]");
  if (!item || event.target.type !== "checkbox" || !currentTask) return;
  try {
    await api.patch(`/projects/${projectId}/tasks/${currentTask.id}/checklist/${item.dataset.checklistId}/toggle`);
    renderChecklist(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/checklist/summary`));
  } catch (error) {
    event.target.checked = !event.target.checked;
    showToast(error.message, "error");
  }
});

document.getElementById("checklist-items").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-checklist-delete]");
  if (!button || !currentTask || !confirm("Xoá mục checklist này?")) return;
  try {
    await api.delete(`/projects/${projectId}/tasks/${currentTask.id}/checklist/${button.dataset.checklistDelete}`);
    renderChecklist(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/checklist/summary`));
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.getElementById("comment-form").querySelector("button").addEventListener("click", async () => {
  const input = document.getElementById("comment-form").querySelector('[name="content"]');
  const content = input.value.trim();
  if (!content || !currentTask) return;
  try {
    await api.post(`/projects/${projectId}/tasks/${currentTask.id}/comments`, { content });
    input.value = "";
    renderComments(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/comments`));
  } catch (error) {
    showToast(error.message, "error");
  }
});

teamButton.addEventListener("click", openTeamDialog);
document.querySelectorAll("[data-close-team]").forEach((button) => button.addEventListener("click", () => teamDialog.close()));
teamDialog.addEventListener("click", (event) => {
  if (event.target === teamDialog) teamDialog.close();
});

async function openTeamDialog() {
  if (!teamDialog.open) teamDialog.showModal();
  const inviteForm = document.getElementById("invite-form");
  inviteForm.hidden = !canManageLists;
  const manager = projectData.user_role === "manager";
  inviteForm.elements.role.querySelector('option[value="manager"]').hidden = manager;
  try {
    const [memberData, invitationData] = await Promise.all([
      api.get(`/projects/${projectId}/members`),
      canManageLists ? api.get(`/projects/${projectId}/invitations`) : Promise.resolve([]),
    ]);
    members = memberData;
    renderMembers();
    renderInvitations(invitationData);
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderMembers() {
  const manager = projectData.user_role === "manager";
  document.getElementById("project-members").innerHTML = members.map((member) => {
    const person = member.user || {};
    const canChange = canManageLists && member.user_id !== currentUser.id && member.role !== "owner"
      && (!manager || member.role !== "manager");
    const canRemove = canChange;
    const roleOptions = manager ? ["member", "viewer"] : ["manager", "member", "viewer"];
    return `<div class="team-row">
      <span class="avatar avatar-small">${escapeHtml(initials(person.full_name || person.email || "?"))}</span>
      <span class="team-person"><strong>${escapeHtml(person.full_name || "Tài khoản")}</strong><small>${escapeHtml(person.email || "")}${person.is_active === false ? " · Đã khoá" : ""}</small></span>
      ${canChange ? `<select data-member-role="${member.user_id}" aria-label="Vai trò của ${escapeHtml(person.full_name || "thành viên")}">${roleOptions.map((role) => `<option value="${role}" ${role === member.role ? "selected" : ""}>${escapeHtml(role)}</option>`).join("")}</select>` : `<span class="role-badge">${escapeHtml(member.role)}</span>`}
      ${canManageLists && projectData.user_role === "owner" && member.role !== "owner" ? `<button class="btn btn-small" type="button" data-transfer-owner="${member.user_id}">Chuyển Owner</button>` : ""}
      ${canRemove ? `<button class="btn btn-small btn-danger" type="button" data-remove-member="${member.user_id}">Xoá</button>` : ""}
    </div>`;
  }).join("") || '<p class="muted">Chưa có thành viên.</p>';
}

function renderInvitations(invitations) {
  const pending = invitations.filter((invitation) => invitation.status === "pending");
  document.getElementById("project-invitations").innerHTML = pending.length ? pending.map((invitation) => `
    <div class="team-row"><span class="team-person"><strong>${escapeHtml(invitation.invitee_email)}</strong><small>${escapeHtml(invitation.role)} · Hết hạn ${escapeHtml(new Date(invitation.expires_at).toLocaleDateString("vi-VN"))}</small></span>
      <button class="btn btn-small btn-danger" type="button" data-cancel-invitation="${invitation.id}">Huỷ</button>
    </div>`).join("") : '<p class="muted">Không có lời mời đang chờ.</p>';
  document.getElementById("project-invitations").dataset.pending = JSON.stringify(pending.map(({ id, role }) => ({ id, role })));
}

document.getElementById("invite-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const invitation = await api.post(`/projects/${projectId}/invitations`, {
      invitee_email: form.elements.invitee_email.value.trim(),
      role: form.elements.role.value,
    });
    const inviteUrl = new URL(`../pages/invitation.html?token=${encodeURIComponent(invitation.raw_token)}`, window.location.href).href;
    const result = document.getElementById("invite-result");
    result.innerHTML = `<strong>Đã tạo lời mời cho ${escapeHtml(invitation.invitee_email)}.</strong><p>Hết hạn: ${escapeHtml(new Date(invitation.expires_at).toLocaleDateString("vi-VN"))}</p><input readonly value="${escapeHtml(inviteUrl)}"><button class="btn btn-small" type="button" id="copy-invite-link">Sao chép liên kết</button><small>Chia sẻ liên kết này an toàn với người được mời; hệ thống chưa cấu hình gửi email tự động.</small>`;
    result.hidden = false;
    document.getElementById("copy-invite-link").addEventListener("click", async () => {
      await navigator.clipboard.writeText(inviteUrl);
      showToast("Đã sao chép liên kết lời mời");
    });
    form.reset();
    await openTeamDialog();
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.getElementById("project-members").addEventListener("change", async (event) => {
  const select = event.target.closest("[data-member-role]");
  if (!select) return;
  try {
    await api.patch(`/projects/${projectId}/members/${select.dataset.memberRole}`, { role: select.value });
    showToast("Đã cập nhật vai trò thành viên");
    await openTeamDialog();
  } catch (error) {
    showToast(error.message, "error");
    await openTeamDialog();
  }
});

document.getElementById("project-members").addEventListener("click", async (event) => {
  const transferButton = event.target.closest("[data-transfer-owner]");
  if (transferButton) {
    const userId = Number(transferButton.dataset.transferOwner);
    const member = members.find((item) => item.user_id === userId);
    if (!member || !confirm(`Chuyển quyền Owner cho ${member.user?.full_name || member.user?.email}? Bạn sẽ trở thành Manager.`)) return;
    try {
      await api.post(`/projects/${projectId}/members/${userId}/transfer-ownership`);
      showToast("Đã chuyển quyền Owner");
      await loadBoard();
      await openTeamDialog();
    } catch (error) {
      showToast(error.message, "error");
    }
    return;
  }
  const button = event.target.closest("[data-remove-member]");
  if (!button) return;
  if (!confirm("Xoá thành viên này khỏi dự án?")) return;
  try {
    await api.delete(`/projects/${projectId}/members/${button.dataset.removeMember}`);
    showToast("Đã xoá thành viên khỏi dự án");
    await openTeamDialog();
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.getElementById("project-invitations").addEventListener("click", async (event) => {
  const cancel = event.target.closest("[data-cancel-invitation]");
  if (!cancel) return;
  const pending = JSON.parse(event.currentTarget.dataset.pending || "[]");
  const invitation = pending.find((item) => item.id === Number(cancel.dataset.cancelInvitation));
  if (projectData.user_role === "manager" && invitation?.role === "manager") {
    showToast("Manager không thể huỷ lời mời dành cho Manager", "error");
    return;
  }
  try {
    await api.delete(`/projects/${projectId}/invitations/${cancel.dataset.cancelInvitation}`);
    showToast("Đã huỷ lời mời");
    await openTeamDialog();
  } catch (error) {
    showToast(error.message, "error");
  }
});

function setProjectTab(tab) {
  const activity = tab === "activity";
  document.querySelector(".board-toolbar").hidden = activity;
  boardElement.hidden = activity;
  document.getElementById("activity-panel").hidden = !activity;
  document.querySelectorAll("[data-project-tab]").forEach((link) => {
    const active = link.dataset.projectTab === tab;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  if (activity) loadActivity();
}

async function loadActivity() {
  const container = document.getElementById("activity-list");
  container.innerHTML = '<p class="muted">Đang tải nhật ký…</p>';
  try {
    const logs = await api.get(`/projects/${projectId}/activity-logs`, { page: 1, size: 100 });
    container.innerHTML = logs.length ? logs.map((log) => `
      <article class="activity-row"><span class="activity-mark">${escapeHtml(initials(log.user_full_name || "U"))}</span>
        <div><strong>${escapeHtml(log.user_full_name || "Tài khoản")}</strong> <span>${escapeHtml(log.action.replaceAll("_", " "))} · ${escapeHtml(log.entity_type)}</span>
          <time>${escapeHtml(formatDateTime(log.created_at))}</time>
          ${log.new_value ? `<details><summary>Chi tiết</summary><pre>${escapeHtml(log.new_value)}</pre></details>` : ""}
        </div></article>`).join("") : '<p class="muted">Chưa có hoạt động nào.</p>';
  } catch (error) {
    container.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}

document.querySelector(".tabs").addEventListener("click", (event) => {
  const link = event.target.closest("[data-project-tab]");
  if (!link) return;
  event.preventDefault();
  if (link.dataset.projectTab === "members") {
    setProjectTab("board");
    window.history.replaceState({}, "", `${window.location.pathname}${window.location.search}#board`);
    openTeamDialog();
    return;
  }
  setProjectTab(link.dataset.projectTab);
  window.history.replaceState({}, "", `${window.location.pathname}${window.location.search}#${link.dataset.projectTab}`);
});


async function handleListAction(action, listId) {
  const list = boardData.lists.find((item) => item.id === listId);
  if (!list) return;
  try {
    if (action === "rename") {
      const name = prompt("Tên danh sách mới:", list.name)?.trim();
      if (!name || name === list.name) return;
      await api.put(`/projects/${projectId}/lists/${listId}`, { name });
    } else if (action === "done") {
      await api.put(`/projects/${projectId}/lists/${listId}`, { is_done_column: !list.is_done_column });
    } else if (action === "delete") {
      const otherLists = boardData.lists.filter((item) => item.id !== listId);
      if (!otherLists.length) return showToast("Dự án phải còn ít nhất một danh sách", "error");
      const target = list.is_done_column ? null : otherLists[0];
      if (list.is_done_column) return showToast("Không thể xoá cột hoàn thành duy nhất", "error");
      if (boardData.tasks.some((task) => task.list_id === listId)) {
        const choices = otherLists.map((item) => `${item.id}: ${item.name}`).join("\n");
        const targetId = Number(prompt(`Chọn ID danh sách nhận công việc:\n${choices}`, String(target.id)));
        if (!otherLists.some((item) => item.id === targetId)) return;
        await api.delete(`/projects/${projectId}/lists/${listId}?target_list_id=${targetId}`);
      } else {
        if (!confirm(`Xoá danh sách "${list.name}"?`)) return;
        await api.delete(`/projects/${projectId}/lists/${listId}`);
      }
    }
    await loadBoard();
  } catch (error) {
    showToast(error.message, "error");
  }
}

boardElement.addEventListener("click", async (event) => {
  const listAction = event.target.closest("[data-list-action]");
  if (listAction) return handleListAction(listAction.dataset.listAction, Number(listAction.dataset.listId));
  const addTask = event.target.closest("[data-create-task]");
  if (addTask) {
    if (!members.length) members = await api.get(`/projects/${projectId}/members`);
    return openTaskForm(Number(addTask.dataset.createTask));
  }
  if (event.target.closest("#add-list-button")) {
    const name = prompt("Tên danh sách mới:")?.trim();
    if (!name) return;
    try {
      await api.post(`/projects/${projectId}/lists`, { name });
      await loadBoard();
    } catch (error) {
      showToast(error.message, "error");
    }
    return;
  }
  const task = event.target.closest(".task-card");
  if (task) openTask(Number(task.dataset.taskId));
});

boardElement.addEventListener("keydown", (event) => {
  if ((event.key === "Enter" || event.key === " ") && event.target.matches(".task-card")) {
    event.preventDefault();
    openTask(Number(event.target.dataset.taskId));
  }
});

let draggedTask = null;
let draggedListId = null;
boardElement.addEventListener("dragstart", (event) => {
  const task = event.target.closest(".task-card");
  const column = event.target.closest(".board-column");
  if (task && canEdit) {
    draggedTask = boardData.tasks.find((item) => item.id === Number(task.dataset.taskId));
    event.dataTransfer.setData("text/task-id", String(task.dataset.taskId));
    event.dataTransfer.effectAllowed = "move";
    requestAnimationFrame(() => task.classList.add("dragging"));
  } else if (column && canManageLists && event.target.closest("[data-list-drag-handle]")) {
    draggedListId = Number(column.dataset.listId);
    event.dataTransfer.setData("text/list-id", String(draggedListId));
    event.dataTransfer.effectAllowed = "move";
  } else {
    event.preventDefault();
  }
});

boardElement.addEventListener("dragend", () => {
  boardElement.querySelectorAll(".dragging, .drop-target").forEach((element) => element.classList.remove("dragging", "drop-target"));
  draggedTask = null;
  draggedListId = null;
});

boardElement.addEventListener("dragover", (event) => {
  const column = event.target.closest(".board-column");
  if (column && (draggedTask || draggedListId)) {
    event.preventDefault();
    column.classList.add("drop-target");
  }
});

boardElement.addEventListener("dragleave", (event) => {
  const column = event.target.closest(".board-column");
  if (column && !column.contains(event.relatedTarget)) column.classList.remove("drop-target");
});

boardElement.addEventListener("drop", async (event) => {
  const column = event.target.closest(".board-column");
  if (!column) return;
  event.preventDefault();
  column.classList.remove("drop-target");
  if (draggedTask && canEdit) {
    const task = draggedTask;
    const targetListId = Number(column.dataset.listId);
    if (task.list_id === targetListId) return;
    const sourceListId = task.list_id;
    task.list_id = targetListId;
    const siblings = boardData.tasks.filter((item) => item.list_id === targetListId && item.id !== task.id);
    task.position = siblings.length;
    renderBoard();
    try {
      await api.patch(`/projects/${projectId}/tasks/${task.id}/move`, { list_id: targetListId, position: task.position });
      await loadBoard();
    } catch (error) {
      showToast(error.message, "error");
      await loadBoard();
    }
    return;
  }
  if (draggedListId && canManageLists) {
    const from = boardData.lists.findIndex((list) => list.id === draggedListId);
    const to = boardData.lists.findIndex((list) => list.id === Number(column.dataset.listId));
    if (from < 0 || to < 0 || from === to) return;
    const previous = [...boardData.lists];
    const [list] = boardData.lists.splice(from, 1);
    boardData.lists.splice(to, 0, list);
    boardData.lists.forEach((item, index) => { item.position = index; });
    renderBoard();
    try {
      await api.patch(`/projects/${projectId}/lists/reorder`, { list_ids: boardData.lists.map((item) => item.id) });
      await loadBoard();
    } catch (error) {
      boardData.lists = previous;
      renderBoard();
      showToast(error.message, "error");
    }
  }
});

newTaskButton.addEventListener("click", async () => {
  if (!members.length) members = await api.get(`/projects/${projectId}/members`);
  openTaskForm(boardData.lists[0]?.id);
});
retryButton.addEventListener("click", loadBoard);
searchInput.addEventListener("input", renderBoard);
priorityFilter.addEventListener("change", renderBoard);
document.querySelector(".header-search input")?.addEventListener("input", (event) => {
  searchInput.value = event.target.value;
  renderBoard();
});

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && projectId && !taskDialog.open) loadBoard();
});
loadBoard();
