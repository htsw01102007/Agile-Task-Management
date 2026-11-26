const boardElement = document.getElementById("board");
const tablePanel = document.getElementById("table-panel");
const tableBody = document.getElementById("project-table-body");
const summaryElement = document.getElementById("board-summary");
const retryButton = document.getElementById("retry-board");
const newTaskButton = document.getElementById("new-task-button");
const teamButton = document.getElementById("team-button");
const searchInput = document.getElementById("task-search");
const priorityFilter = document.getElementById("priority-filter");
const assigneeFilter = document.getElementById("assignee-filter");
const labelFilter = document.getElementById("label-filter");
const labelsManageButton = document.getElementById("labels-manage-button");
const taskDialog = document.getElementById("task-dialog");
const taskForm = document.getElementById("task-form");
const teamDialog = document.getElementById("team-dialog");
const labelsDialog = document.getElementById("labels-dialog");
const trashDialog = document.getElementById("trash-dialog");
const activityUserFilter = document.getElementById("activity-user-filter");
const activityActionFilter = document.getElementById("activity-action-filter");
const activityEntityFilter = document.getElementById("activity-entity-filter");
const priorityNames = { low: "Thấp", medium: "Trung bình", high: "Cao", urgent: "Khẩn cấp" };

const requestedProjectId = new URLSearchParams(window.location.search).get("project");
let projectId = /^\d+$/.test(requestedProjectId || "") ? Number(requestedProjectId) : NaN;
let projectData = null;
let boardData = null;
let currentUser = null;
let members = [];
let projectLabels = [];
let currentTask = null;
let currentChecklistItems = [];
let currentComments = [];
let currentTaskModalTab = "details";
let activityPage = 1;
let activityTotalPages = 1;
const ACTIVITY_PAGE_SIZE = 20;
let savingTask = false;
let canEdit = false;
let canManageLists = false;
let activeTab = "board";

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
  const list = boardData?.lists?.find((item) => item.id === task.list_id);
  if (list) return Boolean(list.is_done_column);
  return Boolean(task.completed_at);
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

const COMMENT_ICON_SVG = '<svg class="icon" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';

function taskMarkup(task) {
  const completed = isTaskDone(task);
  const due = formatDueDate(task.due_date, completed);
  const priority = priorityNames[task.priority] ? task.priority : "medium";
  const labelChips = (task.labels || []).map((lb) => `
    <span class="task-label-chip" style="background:${escapeHtml(lb.label_color || "#64748b")}22;color:${escapeHtml(lb.label_color || "#64748b")};border:1px solid ${escapeHtml(lb.label_color || "#64748b")}55;">
      ${escapeHtml(lb.label_name)}
    </span>`).join("");
  const checklistTotal = Number(task.checklist_total || 0);
  const checklistDone = Number(task.checklist_completed || 0);
  const commentsCount = Number(task.comments_count || 0);
  const attachmentsCount = Number(task.attachments_count || 0);
  const badges = [];
  if (checklistTotal > 0) {
    badges.push(`<span class="task-card-badge${checklistDone === checklistTotal ? " is-complete" : ""}" title="Checklist hoàn thành">${iconSvg("check")}<span>${checklistDone}/${checklistTotal}</span></span>`);
  }
  if (commentsCount > 0) {
    badges.push(`<span class="task-card-badge" title="Số bình luận">${COMMENT_ICON_SVG}<span>${commentsCount}</span></span>`);
  }
  if (attachmentsCount > 0) {
    badges.push(`<span class="task-card-badge" title="Tệp đính kèm">${iconSvg("paperclip")}<span>${attachmentsCount}</span></span>`);
  }
  return `<article class="task-card${completed ? " completed-task" : ""}" tabindex="0" draggable="${canEdit}" data-task-id="${task.id}">
    <div class="task-card-header">
      <span class="task-id-badge">#${task.id}</span>
      <span class="priority priority-${priority}">↑ ${escapeHtml(priorityText(task.priority))}</span>
    </div>
    ${labelChips ? `<div class="task-labels-row">${labelChips}</div>` : ""}
    <h3>${escapeHtml(task.title)}</h3>
    ${task.description ? `<p class="task-desc-preview">${escapeHtml(task.description)}</p>` : ""}
    ${badges.length ? `<div class="task-card-badges">${badges.join("")}</div>` : ""}
    <div class="task-footer">
      <span class="task-date${due.overdue ? " overdue" : ""}">${due.text}</span>
      ${assigneeMarkup(task.assignees)}
    </div>
  </article>`;
}

function populateLabelFilter() {
  if (!labelFilter) return;
  const current = labelFilter.value;
  labelFilter.innerHTML = `<option value="">Mọi nhãn</option>`
    + (projectLabels || []).map((lb) => `<option value="${lb.id}" ${String(lb.id) === current ? "selected" : ""}>${escapeHtml(lb.name)}</option>`).join("");
}

function populateAssigneeFilter() {
  if (!assigneeFilter || !boardData) return;
  const current = assigneeFilter.value;
  const seen = new Map();
  boardData.tasks.forEach((task) => {
    (task.assignees || []).forEach((a) => {
      if (!seen.has(a.user_id)) {
        seen.set(a.user_id, a.user_full_name || a.user_email || `Thành viên #${a.user_id}`);
      }
    });
  });
  assigneeFilter.innerHTML = `<option value="">Mọi thành viên</option><option value="unassigned" ${current === "unassigned" ? "selected" : ""}>Chưa giao cho ai</option>`
    + [...seen.entries()].map(([uid, name]) => `<option value="${uid}" ${String(uid) === current ? "selected" : ""}>${escapeHtml(name)}</option>`).join("");
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
  document.getElementById("project-counts").textContent = `${completed}/${boardData.tasks.length} công việc đã xong`;
}

function getFilteredTasks() {
  const query = searchInput.value.trim().toLocaleLowerCase("vi");
  const selectedPriority = priorityFilter.value;
  const selectedAssignee = assigneeFilter?.value || "";
  const selectedLabel = labelFilter?.value || "";
  return boardData.tasks.filter((task) => {
    const matchQuery = !query
      || task.title.toLocaleLowerCase("vi").includes(query)
      || `#${task.id}`.includes(query);
    const matchPriority = !selectedPriority || task.priority === selectedPriority;
    let matchAssignee = true;
    if (selectedAssignee === "unassigned") {
      matchAssignee = !(task.assignees && task.assignees.length);
    } else if (selectedAssignee) {
      matchAssignee = (task.assignees || []).some((a) => String(a.user_id) === selectedAssignee);
    }
    const matchLabel = !selectedLabel || (task.labels || []).some((lb) => String(lb.label_id) === selectedLabel);
    return matchQuery && matchPriority && matchAssignee && matchLabel;
  });
}

function renderTableView(visibleTasks) {
  if (!tableBody || !boardData) return;
  const listMap = new Map(boardData.lists.map((l) => [l.id, l]));
  if (!visibleTasks.length) {
    tableBody.innerHTML = '<tr><td colspan="6" class="muted">Không có công việc nào khớp bộ lọc.</td></tr>';
    return;
  }
  tableBody.innerHTML = visibleTasks.map((task) => {
    const list = listMap.get(task.list_id);
    const completed = isTaskDone(task);
    const due = formatDueDate(task.due_date, completed);
    return `<tr data-table-task-id="${task.id}" style="cursor:pointer;">
      <td><span class="task-id-badge">#${task.id}</span></td>
      <td><strong>${escapeHtml(task.title)}</strong></td>
      <td><span class="role-badge ${completed ? "status-active" : ""}">${escapeHtml(list?.name || "—")}</span></td>
      <td><span class="priority priority-${escapeHtml(task.priority)}">${escapeHtml(priorityText(task.priority))}</span></td>
      <td>${assigneeMarkup(task.assignees)}</td>
      <td><span class="task-date${due.overdue ? " overdue" : ""}">${escapeHtml(due.text)}</span></td>
    </tr>`;
  }).join("");
}

function renderBoard() {
  if (!boardData) return;

  // Lưu lại vị trí cuộn của bảng và từng cột trước khi cập nhật DOM để chống giật/nháy
  const prevBoardScrollLeft = boardElement.scrollLeft;
  const prevColScrollTops = new Map();
  boardElement.querySelectorAll(".board-column[data-list-id]").forEach((col) => {
    const tasksContainer = col.querySelector(".column-tasks");
    if (tasksContainer) {
      prevColScrollTops.set(col.dataset.listId, tasksContainer.scrollTop);
    }
  });

  populateAssigneeFilter();
  populateLabelFilter();
  const visibleTasks = getFilteredTasks();
  const columns = [...boardData.lists].sort((a, b) => a.position - b.position || a.id - b.id);
  boardElement.innerHTML = columns.map((list) => {
    const tasks = visibleTasks.filter((task) => task.list_id === list.id)
      .sort((a, b) => a.position - b.position || a.id - b.id);
    const content = tasks.length ? tasks.map(taskMarkup).join("")
      : `<p class="board-empty">${visibleTasks.length ? "Chưa có công việc" : "Không có kết quả phù hợp"}</p>`;
    const listActions = canManageLists ? `<span class="column-actions">
      <button type="button" class="column-action" data-list-action="rename" data-list-id="${list.id}" title="Đổi tên cột" aria-label="Đổi tên cột">${iconSvg("edit")}</button>
      <button type="button" class="column-action" data-list-action="done" data-list-id="${list.id}" title="Đặt làm cột Hoàn thành" aria-label="Đặt cột hoàn thành">${list.is_done_column ? iconSvg("check") : iconSvg("circle")}</button>
      <button type="button" class="column-action" data-list-action="delete" data-list-id="${list.id}" title="Xoá cột" aria-label="Xoá cột">${iconSvg("trash")}</button>
    </span>` : "";
    const addTask = canEdit ? `<button type="button" class="add-task" data-create-task="${list.id}">${iconSvg("plus")} <span>Thêm công việc vào cột này</span></button>` : "";
    const gripHandle = canManageLists
      ? `<span class="column-grip" title="Giữ và kéo để đổi vị trí cột" aria-hidden="true">${iconSvg("grip")}</span>`
      : "";
    return `<section class="board-column${list.is_done_column ? " board-column-done" : ""}" data-list-id="${list.id}" aria-label="${escapeHtml(list.name)}" draggable="${canManageLists}">
      <div class="column-title" ${canManageLists ? 'data-list-drag-handle="true" title="Giữ tiêu đề cột và kéo sang trái/phải để đổi thứ tự"' : ""}>${gripHandle}<span class="column-dot${list.is_done_column ? " done-dot" : ""}"></span><strong>${escapeHtml(list.name)}</strong><span class="count">${tasks.length}</span>${listActions}</div>
      <div class="column-tasks">${content}</div>${addTask}
    </section>`;
  }).join("") + (canManageLists ? `<button type="button" id="add-list-button" class="add-list">${iconSvg("plus")} <span>Thêm cột trạng thái mới</span></button>` : "");

  // Khôi phục vị trí cuộn ngay trong cùng frame
  boardElement.scrollLeft = prevBoardScrollLeft;
  boardElement.querySelectorAll(".board-column[data-list-id]").forEach((col) => {
    const savedTop = prevColScrollTops.get(col.dataset.listId);
    const tasksContainer = col.querySelector(".column-tasks");
    if (tasksContainer && typeof savedTop === "number") {
      tasksContainer.scrollTop = savedTop;
    }
  });

  renderTableView(visibleTasks);
  renderStatsView();

  const completedCount = boardData.tasks.filter(isTaskDone).length;
  summaryElement.textContent = `${boardData.lists.length} cột · Hiển thị ${visibleTasks.length}/${boardData.tasks.length} công việc · Tiến độ ${boardData.tasks.length ? Math.round(completedCount / boardData.tasks.length * 100) : 0}%`;
  renderInsights();
}

function renderStatsView() {
  if (!boardData) return;
  const statsPanel = document.getElementById("stats-panel");
  if (!statsPanel) return;

  const allTasks = boardData.tasks || [];
  const totalTasks = allTasks.length;
  const now = Date.now();
  const completedTasks = allTasks.filter(isTaskDone).length;
  const activeTasks = Math.max(0, totalTasks - completedTasks);
  const overdueTasks = allTasks.filter((t) => !isTaskDone(t) && t.due_date && new Date(t.due_date).getTime() < now).length;

  const donePct = totalTasks ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const activePct = totalTasks ? Math.round((activeTasks / totalTasks) * 100) : 0;
  const overduePct = totalTasks ? Math.min(100, Math.round((overdueTasks / totalTasks) * 100)) : 0;

  const doneLabel = document.getElementById("proj-stat-done-label");
  const activeLabel = document.getElementById("proj-stat-active-label");
  const overdueLabel = document.getElementById("proj-stat-overdue-label");
  if (doneLabel) doneLabel.textContent = `${completedTasks}/${totalTasks} việc (${donePct}%)`;
  if (activeLabel) activeLabel.textContent = `${activeTasks} việc (${activePct}%)`;
  if (overdueLabel) overdueLabel.textContent = `${overdueTasks} việc`;

  const doneBar = document.getElementById("proj-stat-done-bar");
  const activeBar = document.getElementById("proj-stat-active-bar");
  const overdueBar = document.getElementById("proj-stat-overdue-bar");
  if (doneBar) doneBar.style.width = `${donePct}%`;
  if (activeBar) activeBar.style.width = `${activePct}%`;
  if (overdueBar) overdueBar.style.width = `${overduePct}%`;

  // Xây dựng danh sách thành viên kết hợp từ members API và assignees trong tasks
  const memberMap = new Map();
  (members || []).forEach((m) => {
    const u = m.user || {};
    memberMap.set(m.user_id, {
      user_id: m.user_id,
      full_name: u.full_name || u.email || `Thành viên #${m.user_id}`,
      email: u.email || "",
      avatar_url: u.avatar_url || null,
      role: m.role || "member",
      tasks: [],
    });
  });

  const unassignedTasks = [];
  allTasks.forEach((task) => {
    const assignees = task.assignees || [];
    if (!assignees.length) {
      unassignedTasks.push(task);
      return;
    }
    assignees.forEach((a) => {
      if (!memberMap.has(a.user_id)) {
        memberMap.set(a.user_id, {
          user_id: a.user_id,
          full_name: a.user_full_name || a.user_email || `Thành viên #${a.user_id}`,
          email: a.user_email || "",
          avatar_url: a.user_avatar_url || null,
          role: "member",
          tasks: [],
        });
      }
      memberMap.get(a.user_id).tasks.push(task);
    });
  });

  const summarySpan = document.getElementById("member-stats-summary");
  if (summarySpan) {
    summarySpan.textContent = `${memberMap.size} thành viên · Tổng ${totalTasks} công việc trong dự án`;
  }

  const container = document.getElementById("member-stats-list");
  if (!container) return;

  const memberList = [...memberMap.values()].sort((a, b) => b.tasks.length - a.tasks.length);
  if (unassignedTasks.length > 0) {
    memberList.push({
      user_id: "unassigned",
      full_name: "Chưa giao cho thành viên",
      email: "Các công việc chưa chỉ định người thực hiện",
      avatar_url: null,
      role: "unassigned",
      tasks: unassignedTasks,
    });
  }

  if (!memberList.length) {
    container.innerHTML = '<p class="empty-state">Chưa có dữ liệu thành viên trong dự án.</p>';
    return;
  }

  const roleLabels = {
    owner: "Owner",
    manager: "Manager",
    member: "Member",
    viewer: "Viewer",
    unassigned: "Chưa phân công",
  };

  container.innerHTML = memberList.map((m) => {
    const mTotal = m.tasks.length;
    const mDone = m.tasks.filter(isTaskDone).length;
    const mActive = Math.max(0, mTotal - mDone);
    const mOverdue = m.tasks.filter((t) => !isTaskDone(t) && t.due_date && new Date(t.due_date).getTime() < now).length;

    // Tỷ lệ khối lượng công việc của thành viên so với tổng công việc toàn dự án
    const sharePct = totalTasks ? Math.round((mTotal / totalTasks) * 100) : 0;
    // Tỷ lệ hoàn thành trên số việc thành viên được giao
    const memberDonePct = mTotal ? Math.round((mDone / mTotal) * 100) : 0;
    const memberActivePct = mTotal ? Math.round((mActive / mTotal) * 100) : 0;
    const memberOverduePct = mTotal ? Math.min(100, Math.round((mOverdue / mTotal) * 100)) : 0;

    const avatarHtml = m.avatar_url
      ? `<img class="avatar avatar-small" src="${escapeHtml(m.avatar_url)}" alt="${escapeHtml(m.full_name)}">`
      : `<span class="avatar avatar-small">${escapeHtml(m.user_id === "unassigned" ? "?" : initials(m.full_name))}</span>`;

    return `<article class="member-stat-card">
      <div class="member-stat-header">
        <div class="member-stat-user">
          ${avatarHtml}
          <div>
            <strong>${escapeHtml(m.full_name)}</strong>
            ${m.email ? `<small>${escapeHtml(m.email)}</small>` : ""}
          </div>
        </div>
        <div class="member-stat-badges">
          <span class="role-badge">${escapeHtml(roleLabels[m.role] || m.role)}</span>
          <span class="stat-pill"><strong>${sharePct}%</strong>&nbsp;khối lượng dự án (${mTotal}/${totalTasks} việc)</span>
        </div>
      </div>

      <div class="health-bars member-health-bars">
        <div class="health-row">
          <div class="health-row-top">
            <span>Tỷ lệ đảm nhận trong dự án</span>
            <span>${mTotal}/${totalTasks} việc (${sharePct}%)</span>
          </div>
          <div class="health-track">
            <div class="health-fill" style="width: ${sharePct}%; background: #8b5cf6;"></div>
          </div>
        </div>

        <div class="health-row">
          <div class="health-row-top">
            <span>Hoàn thành</span>
            <span>${mDone}/${mTotal} việc (${memberDonePct}%)</span>
          </div>
          <div class="health-track">
            <div class="health-fill" style="width: ${memberDonePct}%; background: var(--ok);"></div>
          </div>
        </div>

        <div class="health-row">
          <div class="health-row-top">
            <span>Đang triển khai</span>
            <span>${mActive} việc (${memberActivePct}%)</span>
          </div>
          <div class="health-track">
            <div class="health-fill" style="width: ${memberActivePct}%; background: var(--accent);"></div>
          </div>
        </div>

        <div class="health-row">
          <div class="health-row-top">
            <span>Quá hạn cần xử lý</span>
            <span>${mOverdue} việc</span>
          </div>
          <div class="health-track">
            <div class="health-fill" style="width: ${memberOverduePct}%; background: var(--err);"></div>
          </div>
        </div>
      </div>
    </article>`;
  }).join("");
}

function renderProject() {
  document.title = `${projectData.name} | Agile Workspace`;
  document.getElementById("project-title").textContent = projectData.name;
  document.getElementById("project-crumb").textContent = projectData.name;
  document.getElementById("project-description").textContent = projectData.description || "Chưa có mô tả chi tiết cho dự án này.";
  document.getElementById("project-mark").textContent = initials(projectData.name);
  document.getElementById("project-status").textContent = statusText(projectData.status);
  const roleBadge = document.getElementById("project-role-badge");
  if (roleBadge) roleBadge.textContent = `Vai trò: ${(projectData.user_role || "member").toUpperCase()}`;

  const active = projectData.status === "active";
  canEdit = active && ["owner", "manager", "member"].includes(projectData.user_role);
  canManageLists = active && ["owner", "manager"].includes(projectData.user_role);
  document.getElementById("readonly-banner").hidden = active;
  newTaskButton.hidden = !canEdit;
  teamButton.hidden = !["owner", "manager"].includes(projectData.user_role);
  if (labelsManageButton) labelsManageButton.hidden = !canManageLists;
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

async function loadBoard({ showSkeleton = false } = {}) {
  // Chỉ hiện khung xương (skeleton) ở lần tải đầu tiên khi chưa có dữ liệu bảng
  if (!boardData || showSkeleton) {
    renderLoading();
  }
  try {
    const id = await resolveProjectId();
    const [project, board, user, memberList, labelList] = await Promise.all([
      api.get(`/projects/${id}`),
      api.get(`/projects/${id}/board`),
      currentUser ? Promise.resolve(currentUser) : api.get("/auth/me"),
      api.get(`/projects/${id}/members`).catch(() => members),
      api.get(`/projects/${id}/labels`).catch(() => projectLabels),
    ]);
    projectData = project;
    boardData = board;
    currentUser = user;
    if (Array.isArray(memberList)) members = memberList;
    if (Array.isArray(labelList)) projectLabels = labelList;
    renderProject();
    renderBoard();
    connectProjectWebSocket(id);
    if (window.location.hash === "#activity") setProjectTab("activity");
    else if (window.location.hash === "#table") setProjectTab("table");
    else if (window.location.hash === "#stats") setProjectTab("stats");
    boardElement.setAttribute("aria-busy", "false");
    const taskId = Number(new URLSearchParams(window.location.search).get("task"));
    if (Number.isSafeInteger(taskId) && taskId > 0 && !taskDialog.open) await openTask(taskId, false);
  } catch (error) {
    boardElement.setAttribute("aria-busy", "false");
    if (!boardData) {
      const loginLink = error.status === 401
        ? `<a href="../pages/login.html?next=${encodeURIComponent(window.location.pathname + window.location.search)}">Đăng nhập để xem bảng dự án</a>`
        : '<a href="../index.html">Về danh sách dự án</a>';
      boardElement.innerHTML = `<div class="board-load-error"><strong>Không tải được bảng công việc.</strong><span>${escapeHtml(error.message)}</span>${loginLink}</div>`;
      summaryElement.textContent = "Đã xảy ra lỗi khi tải dữ liệu.";
      retryButton.hidden = false;
    }
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

let pickedAssigneeIds = new Set();
let pickedLabelIds = new Set();
let editingInlineLabelId = null;

function selectedAssigneeIds() {
  return [...pickedAssigneeIds];
}

function selectedLabelIds() {
  return [...pickedLabelIds];
}

function populateTaskLists(selectedId) {
  taskForm.elements.list_id.innerHTML = boardData.lists
    .map((list) => `<option value="${list.id}" ${list.id === selectedId ? "selected" : ""}>${escapeHtml(list.name)}</option>`)
    .join("");
}

function updateAssigneeCountBadge() {
  const countEl = document.getElementById("assignee-picked-count");
  if (countEl) {
    countEl.textContent = pickedAssigneeIds.size ? `${pickedAssigneeIds.size} đã chọn` : "Chưa chọn";
    countEl.classList.toggle("has-value", pickedAssigneeIds.size > 0);
  }
}

function renderAssigneePickerList() {
  const container = document.getElementById("task-assignees-list");
  if (!container) return;
  const assignable = members.filter((member) => member.role !== "viewer" && member.user?.is_active !== false);
  updateAssigneeCountBadge();
  if (!assignable.length) {
    container.innerHTML = '<p class="picker-empty muted">Chưa có thành viên đủ quyền nhận việc.</p>';
    return;
  }
  const roleMap = { owner: "Owner", manager: "Manager", member: "Member" };
  container.innerHTML = assignable.map((member) => {
    const uid = Number(member.user_id);
    const selected = pickedAssigneeIds.has(uid);
    const name = member.user?.full_name || member.user?.email || `Thành viên #${uid}`;
    const avatar = member.user?.avatar_url
      ? `<img class="picker-avatar" src="${escapeHtml(member.user.avatar_url)}" alt="${escapeHtml(name)}">`
      : `<span class="picker-avatar">${escapeHtml(initials(name))}</span>`;
    return `<button type="button" class="picker-item${selected ? " is-selected" : ""}" data-pick-assignee="${uid}" aria-pressed="${selected}" ${!canEdit ? "disabled" : ""}>
      ${avatar}
      <span class="picker-item-info">
        <strong>${escapeHtml(name)}</strong>
        <small>${escapeHtml(roleMap[member.role] || member.role)}</small>
      </span>
      <span class="picker-check" aria-hidden="true">${selected ? iconSvg("check") : ""}</span>
    </button>`;
  }).join("");
}

function populateAssignees(selectedIds = []) {
  pickedAssigneeIds = new Set(selectedIds.map(Number));
  renderAssigneePickerList();
}

function updateLabelCountBadge() {
  const countEl = document.getElementById("label-picked-count");
  if (countEl) {
    countEl.textContent = pickedLabelIds.size ? `${pickedLabelIds.size} đã chọn` : "Chưa chọn";
    countEl.classList.toggle("has-value", pickedLabelIds.size > 0);
  }
}

function closeInlineLabelEditor() {
  editingInlineLabelId = null;
  const editor = document.getElementById("inline-label-editor");
  const nameInput = document.getElementById("inline-label-name");
  if (editor) editor.hidden = true;
  if (nameInput) {
    nameInput.value = "";
    clearFieldError(nameInput);
  }
}

function openInlineLabelEditor(label = null) {
  const editor = document.getElementById("inline-label-editor");
  const titleEl = document.getElementById("inline-label-editor-title");
  const nameInput = document.getElementById("inline-label-name");
  const colorInput = document.getElementById("inline-label-color");
  if (!editor || !nameInput || !colorInput) return;

  editingInlineLabelId = label ? Number(label.id) : null;
  if (titleEl) titleEl.textContent = label ? `Chỉnh sửa nhãn "${label.name}"` : "Tạo nhãn phân loại mới";
  nameInput.value = label?.name || "";
  const colorVal = (label?.color || "#5E6AD2").toUpperCase();
  colorInput.value = /^#[0-9A-F]{6}$/i.test(colorVal) ? colorVal : "#5E6AD2";
  syncInlineColorSwatches(colorInput.value);
  clearFieldError(nameInput);
  editor.hidden = false;
  nameInput.focus();
}

function syncInlineColorSwatches(activeHex) {
  const normalized = (activeHex || "").toUpperCase();
  document.querySelectorAll("#inline-label-swatches .color-swatch").forEach((btn) => {
    btn.classList.toggle("active", (btn.dataset.swatch || "").toUpperCase() === normalized);
  });
}

function renderLabelPickerList() {
  const container = document.getElementById("task-labels-list");
  const toggleCreateBtn = document.getElementById("toggle-inline-label-btn");
  if (toggleCreateBtn) toggleCreateBtn.hidden = !canManageLists;
  updateLabelCountBadge();
  if (!container) return;

  if (!projectLabels.length) {
    container.innerHTML = `<p class="picker-empty muted">${canManageLists ? 'Chưa có nhãn nào. Nhấn "＋ Tạo nhãn" để thêm mới.' : "Dự án chưa có nhãn phân loại."}</p>`;
    return;
  }

  container.innerHTML = projectLabels.map((lb) => {
    const lid = Number(lb.id);
    const selected = pickedLabelIds.has(lid);
    const color = lb.color || "#64748b";
    return `<div class="label-picker-row${selected ? " is-selected" : ""}" style="--lb-color:${escapeHtml(color)};">
      <button type="button" class="label-pick-main" data-pick-label="${lid}" aria-pressed="${selected}" ${!canEdit ? "disabled" : ""}>
        <span class="label-color-dot" style="background:${escapeHtml(color)};"></span>
        <span class="label-pick-name">${escapeHtml(lb.name)}</span>
        <span class="picker-check" aria-hidden="true">${selected ? iconSvg("check") : ""}</span>
      </button>
      ${canManageLists ? `<span class="label-inline-tools">
        <button type="button" class="column-action" data-inline-edit-label="${lid}" title="Đổi tên / màu nhãn" aria-label="Sửa nhãn">${iconSvg("edit")}</button>
        <button type="button" class="column-action danger-icon" data-inline-delete-label="${lid}" title="Xoá nhãn khỏi dự án" aria-label="Xoá nhãn">${iconSvg("trash")}</button>
      </span>` : ""}
    </div>`;
  }).join("");
}

function populateLabels(selectedIds = []) {
  pickedLabelIds = new Set(selectedIds.map(Number));
  closeInlineLabelEditor();
  renderLabelPickerList();
}

function setTaskFormReadOnly(readOnly) {
  taskForm.querySelectorAll("input:not(#inline-label-name):not(#inline-label-color), textarea, select").forEach((input) => {
    input.disabled = readOnly;
  });
  taskForm.querySelectorAll("[data-pick-assignee], [data-pick-label]").forEach((btn) => {
    btn.disabled = readOnly;
  });
  document.getElementById("task-submit").hidden = readOnly;
}

function openTaskForm(listId, task = null) {
  currentTask = task;
  taskForm.reset();
  document.getElementById("task-dialog-title").textContent = task ? task.title : "Tạo công việc mới";
  document.getElementById("task-dialog-context").textContent = task ? `CÔNG VIỆC #${task.id}` : "KHỞI TẠO CÔNG VIỆC";
  document.getElementById("task-submit").textContent = task ? "Lưu thay đổi" : "Tạo công việc";
  document.getElementById("task-delete").hidden = !task || !canDeleteTask(task);
  document.getElementById("task-completed-at").textContent = task?.completed_at ? `Hoàn thành: ${formatDueDate(task.completed_at, true).text}` : "";
  document.getElementById("task-created-by").textContent = task ? `Mã người tạo: #${task.created_by}` : "";
  taskForm.elements.title.value = task?.title || "";
  taskForm.elements.description.value = task?.description || "";
  taskForm.elements.priority.value = task?.priority || "medium";
  taskForm.elements.start_date.value = toDateTimeInput(task?.start_date);
  taskForm.elements.due_date.value = toDateTimeInput(task?.due_date);
  populateTaskLists(task?.list_id || listId || boardData.lists[0]?.id);
  populateAssignees((task?.assignees || []).map((assignee) => assignee.user_id));
  populateLabels((task?.labels || []).map((lb) => lb.label_id));
  const taskModalTabs = document.getElementById("task-modal-tabs");
  if (taskModalTabs) taskModalTabs.hidden = !task;
  setTaskModalTab("details", Boolean(task));
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
    const [task, memberList, labelList] = await Promise.all([
      api.get(`/projects/${projectId}/tasks/${taskId}`),
      members.length ? Promise.resolve(members) : api.get(`/projects/${projectId}/members`),
      projectLabels.length ? Promise.resolve(projectLabels) : api.get(`/projects/${projectId}/labels`),
    ]);
    members = memberList;
    projectLabels = labelList;
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

async function syncLabels(taskId, selectedIds) {
  const currentIds = new Set((currentTask?.labels || []).map((lb) => lb.label_id));
  const desiredIds = new Set(selectedIds);
  const addIds = [...desiredIds].filter((id) => !currentIds.has(id));
  const removeIds = [...currentIds].filter((id) => !desiredIds.has(id));
  if (addIds.length) await api.post(`/projects/${projectId}/tasks/${taskId}/labels`, { label_ids: addIds });
  for (const id of removeIds) await api.delete(`/projects/${projectId}/tasks/${taskId}/labels/${id}`);
}

// Click chọn / bỏ chọn người thực hiện
document.getElementById("task-assignees-list")?.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-pick-assignee]");
  if (!btn || btn.disabled || !canEdit) return;
  const uid = Number(btn.dataset.pickAssignee);
  if (pickedAssigneeIds.has(uid)) pickedAssigneeIds.delete(uid);
  else pickedAssigneeIds.add(uid);
  renderAssigneePickerList();
});

// Tích hợp chọn / bỏ chọn nhãn + Quản lý nhãn (Tạo / Sửa / Xoá) ngay trong mục Nhãn phân loại
document.getElementById("toggle-inline-label-btn")?.addEventListener("click", () => {
  const editor = document.getElementById("inline-label-editor");
  if (editor && !editor.hidden && editingInlineLabelId === null) {
    closeInlineLabelEditor();
  } else {
    openInlineLabelEditor(null);
  }
});

document.getElementById("inline-label-cancel")?.addEventListener("click", closeInlineLabelEditor);

document.getElementById("inline-label-swatches")?.addEventListener("click", (event) => {
  const swatch = event.target.closest("[data-swatch]");
  if (!swatch) return;
  const colorInput = document.getElementById("inline-label-color");
  if (colorInput) {
    colorInput.value = swatch.dataset.swatch;
    syncInlineColorSwatches(colorInput.value);
  }
});

document.getElementById("inline-label-color")?.addEventListener("input", (event) => {
  syncInlineColorSwatches(event.target.value);
});

document.getElementById("inline-label-name")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    document.getElementById("inline-label-save")?.click();
  } else if (event.key === "Escape") {
    event.preventDefault();
    closeInlineLabelEditor();
  }
});

document.getElementById("inline-label-save")?.addEventListener("click", async () => {
  const nameInput = document.getElementById("inline-label-name");
  const colorInput = document.getElementById("inline-label-color");
  const saveBtn = document.getElementById("inline-label-save");
  if (!nameInput || !colorInput) return;

  const name = nameInput.value.trim();
  const color = (colorInput.value || "#5E6AD2").toUpperCase();
  if (!name) {
    setFieldError(nameInput, "Vui lòng nhập tên nhãn.");
    nameInput.focus();
    return;
  }
  clearFieldError(nameInput);
  if (saveBtn) saveBtn.disabled = true;

  try {
    if (editingInlineLabelId) {
      const updated = await api.put(`/projects/${projectId}/labels/${editingInlineLabelId}`, { name, color });
      projectLabels = projectLabels.map((lb) => (lb.id === updated.id ? updated : lb));
      if (boardData?.tasks) {
        boardData.tasks.forEach((t) => {
          (t.labels || []).forEach((tl) => {
            if (tl.label_id === updated.id) {
              tl.label_name = updated.name;
              tl.label_color = updated.color;
            }
          });
        });
        renderBoard();
      }
      populateLabelFilter();
      closeInlineLabelEditor();
      renderLabelPickerList();
      showToast(`Đã cập nhật nhãn "${updated.name}"`);
    } else {
      const created = await api.post(`/projects/${projectId}/labels`, { name, color });
      projectLabels.push(created);
      pickedLabelIds.add(Number(created.id));
      populateLabelFilter();
      closeInlineLabelEditor();
      renderLabelPickerList();
      showToast(`Đã tạo và chọn nhãn "${created.name}"`);
    }
  } catch (error) {
    setFieldError(nameInput, error.message);
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
});

document.getElementById("task-labels-list")?.addEventListener("click", async (event) => {
  const pickBtn = event.target.closest("[data-pick-label]");
  if (pickBtn) {
    if (pickBtn.disabled || !canEdit) return;
    const lid = Number(pickBtn.dataset.pickLabel);
    if (pickedLabelIds.has(lid)) pickedLabelIds.delete(lid);
    else pickedLabelIds.add(lid);
    renderLabelPickerList();
    return;
  }

  const editBtn = event.target.closest("[data-inline-edit-label]");
  if (editBtn && canManageLists) {
    const label = projectLabels.find((lb) => lb.id === Number(editBtn.dataset.inlineEditLabel));
    if (label) openInlineLabelEditor(label);
    return;
  }

  const deleteBtn = event.target.closest("[data-inline-delete-label]");
  if (deleteBtn && canManageLists) {
    const lid = Number(deleteBtn.dataset.inlineDeleteLabel);
    const label = projectLabels.find((lb) => lb.id === lid);
    if (!label) return;
    const ok = await showConfirmModal({
      eyebrow: "QUẢN LÝ NHÃN",
      title: `Xoá nhãn "${label.name}"?`,
      message: "Nhãn sẽ bị gỡ khỏi tất cả công việc trong dự án và không thể hoàn tác.",
      confirmText: "Xoá nhãn",
      danger: true,
    });
    if (!ok) return;
    try {
      await api.delete(`/projects/${projectId}/labels/${lid}`);
      projectLabels = projectLabels.filter((lb) => lb.id !== lid);
      pickedLabelIds.delete(lid);
      if (editingInlineLabelId === lid) closeInlineLabelEditor();
      if (currentTask) {
        currentTask.labels = (currentTask.labels || []).filter((tl) => tl.label_id !== lid);
      }
      if (labelFilter && labelFilter.value === String(lid)) labelFilter.value = "";
      if (boardData?.tasks) {
        boardData.tasks.forEach((t) => {
          t.labels = (t.labels || []).filter((tl) => tl.label_id !== lid);
        });
        renderBoard();
      }
      populateLabelFilter();
      renderLabelPickerList();
      showToast(`Đã xoá nhãn "${label.name}"`);
    } catch (error) {
      showToast(error.message, "error");
    }
  }
});

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (savingTask || !canEdit) return;
  const submitButton = document.getElementById("task-submit");
  savingTask = true;
  submitButton.disabled = true;
  try {
    const payload = buildTaskPayload();
    if (payload.start_date && payload.due_date && new Date(payload.due_date) < new Date(payload.start_date)) {
      setFieldError(taskForm.elements.due_date, "Hạn hoàn thành không được sớm hơn thời gian bắt đầu.");
      return;
    }
    if (currentTask) {
      const taskId = currentTask.id;
      const assigneeIds = selectedAssigneeIds();
      const labelIds = selectedLabelIds();
      await api.put(`/projects/${projectId}/tasks/${taskId}`, payload);
      try {
        await syncAssignees(taskId, assigneeIds);
        await syncLabels(taskId, labelIds);
      } catch (error) {
        showToast(`Đã lưu công việc nhưng chưa cập nhật người thực hiện/nhãn: ${error.message}`, "error");
        await openTask(taskId, false);
        await loadBoard();
        return;
      }
      showToast("Đã cập nhật công việc");
      closeTaskDialog();
      await loadBoard();
    } else {
      payload.assignee_ids = selectedAssigneeIds();
      payload.label_ids = selectedLabelIds();
      const created = await api.post(`/projects/${projectId}/tasks`, payload);
      showToast("Đã tạo công việc");
      closeTaskDialog();
      await loadBoard();
      await openTask(created.id);
    }
  } catch (error) {
    if (!applyApiErrorsToForm(taskForm, error)) {
      showToast(error.message, "error");
    }
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
  const ok = await showConfirmModal({
    eyebrow: "XOÁ CÔNG VIỆC",
    title: `Xoá "${currentTask.title}"?`,
    message: "Công việc sẽ được chuyển vào thùng rác của dự án và có thể khôi phục lại sau.",
    confirmText: "Chuyển vào thùng rác",
    danger: true,
  });
  if (!ok) return;
  try {
    await api.delete(`/projects/${projectId}/tasks/${currentTask.id}`);
    showToast("Đã chuyển công việc vào thùng rác");
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
      <div class="team-row"><span class="team-person"><strong>#${task.id} · ${escapeHtml(task.title)}</strong><small>Đã xoá ${escapeHtml(task.deleted_at ? formatDateTime(task.deleted_at) : "")}</small></span><button class="btn btn-small btn-primary" type="button" data-restore-task="${task.id}">Khôi phục</button></div>`).join("")
      : '<p class="empty-state">Thùng rác đang trống.</p>';
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

function setTaskModalTab(tab, hasTask = Boolean(currentTask)) {
  currentTaskModalTab = tab;
  const showDetails = hasTask && tab === "details";
  const showActivity = hasTask && tab === "activity";
  ["checklist-panel", "comments-panel", "attachments-panel"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.hidden = !showDetails;
  });
  const taskActivityPanel = document.getElementById("task-activity-panel");
  if (taskActivityPanel) taskActivityPanel.hidden = !showActivity;
  document.querySelectorAll("[data-task-modal-tab]").forEach((btn) => {
    const active = btn.dataset.taskModalTab === tab;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-selected", active ? "true" : "false");
  });
  if (showActivity && currentTask) {
    loadTaskActivity(currentTask.id);
  }
}

document.getElementById("task-modal-tabs")?.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-task-modal-tab]");
  if (!btn || !currentTask) return;
  setTaskModalTab(btn.dataset.taskModalTab, true);
});

async function loadTaskActivity(taskId) {
  const container = document.getElementById("task-activity-list");
  if (!container) return;
  container.innerHTML = '<p class="muted">Đang tải lịch sử hoạt động…</p>';
  try {
    const logs = await api.get(`/projects/${projectId}/activity-logs`, { task_id: taskId, page: 1, size: 50 });
    if (!currentTask || currentTask.id !== taskId) return;
    container.innerHTML = logs.length ? logs.map(activityLogRowMarkup).join("")
      : '<p class="muted">Chưa có hoạt động nào cho công việc này.</p>';
  } catch (error) {
    container.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}

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
    if (currentTaskModalTab === "activity") {
      loadTaskActivity(taskId);
    }
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderChecklist(summary) {
  const completedCount = summary.completed_items || 0;
  const totalCount = summary.total_items || 0;
  const pct = Math.round(summary.progress_percent || 0);
  currentChecklistItems = summary.items || [];
  const badge = document.getElementById("checklist-progress");
  if (badge) {
    badge.textContent = `${completedCount}/${totalCount} · ${pct}%`;
    badge.classList.toggle("status-active", pct >= 100 && totalCount > 0);
  }
  const fill = document.getElementById("checklist-progress-fill");
  if (fill) {
    fill.style.width = `${pct}%`;
    fill.style.background = pct >= 100 && totalCount > 0 ? "var(--ok)" : "var(--accent)";
  }
  document.getElementById("checklist-items").innerHTML = currentChecklistItems.length ? currentChecklistItems.map((item, idx) => `
    <div class="checklist-item${item.is_done ? " is-done" : ""}" data-checklist-id="${item.id}">
      <input type="checkbox" ${item.is_done ? "checked" : ""} ${canEdit ? "" : "disabled"}>
      <span class="checklist-item-text">${escapeHtml(item.content)}</span>
      ${canEdit ? `<span class="checklist-actions">
        <button type="button" class="column-action" data-checklist-move="up" data-checklist-id="${item.id}" title="Đưa lên trên" aria-label="Đưa lên trên" ${idx === 0 ? "disabled" : ""}>${iconSvg("chevronUp")}</button>
        <button type="button" class="column-action icon-rotate-down" data-checklist-move="down" data-checklist-id="${item.id}" title="Đưa xuống dưới" aria-label="Đưa xuống dưới" ${idx === currentChecklistItems.length - 1 ? "disabled" : ""}>${iconSvg("chevronUp")}</button>
        <button type="button" class="column-action" data-checklist-edit="${item.id}" title="Sửa mục" aria-label="Sửa mục">${iconSvg("edit")}</button>
        <button type="button" class="column-action danger-icon" data-checklist-delete="${item.id}" title="Xoá mục" aria-label="Xoá mục">${iconSvg("trash")}</button>
      </span>` : ""}
    </div>`).join("") : '<p class="checklist-empty muted">Chưa có mục kiểm tra nào cho công việc này.</p>';
  document.getElementById("checklist-form").hidden = !canEdit;
}

function renderComments(comments) {
  currentComments = comments || [];
  const countBadge = document.getElementById("comments-count-badge");
  if (countBadge) countBadge.textContent = `${currentComments.length} bình luận`;

  document.getElementById("task-comments").innerHTML = currentComments.length ? currentComments.map((comment) => {
    const isAuthor = Number(comment.user_id) === Number(currentUser?.id);
    const canEditComment = canEdit && isAuthor;
    const canDeleteComment = canEdit && (isAuthor || projectData?.user_role === "owner");
    const isEdited = comment.updated_at && comment.created_at && new Date(comment.updated_at).getTime() - new Date(comment.created_at).getTime() > 2000;
    const authorName = comment.user_full_name || comment.user_email || "Tài khoản";
    const avatarMarkup = comment.user_avatar_url
      ? `<img class="comment-avatar" src="${escapeHtml(comment.user_avatar_url)}" alt="${escapeHtml(authorName)}">`
      : `<span class="comment-avatar">${escapeHtml(initials(authorName))}</span>`;

    return `<article class="task-comment${isAuthor ? " is-own" : ""}" data-comment-id="${comment.id}">
      ${avatarMarkup}
      <div class="task-comment-body">
        <div class="comment-header">
          <div class="comment-meta">
            <strong>${escapeHtml(authorName)}</strong>
            ${isAuthor ? '<span class="comment-you-tag">Bạn</span>' : ""}
            <time>${escapeHtml(formatDateTime(comment.created_at))}${isEdited ? " · đã chỉnh sửa" : ""}</time>
          </div>
          ${(canEditComment || canDeleteComment) ? `<span class="comment-actions">
            ${canEditComment ? `<button type="button" class="comment-action-btn" data-comment-edit="${comment.id}">${iconSvg("edit")} <span>Sửa</span></button>` : ""}
            ${canDeleteComment ? `<button type="button" class="comment-action-btn danger" data-comment-delete="${comment.id}">${iconSvg("trash")} <span>Xoá</span></button>` : ""}
          </span>` : ""}
        </div>
        <p class="comment-content">${escapeHtml(comment.content)}</p>
      </div>
    </article>`;
  }).join("") : '<p class="checklist-empty muted">Chưa có bình luận nào. Hãy mở đầu cuộc trao đổi!</p>';
  document.getElementById("comment-form").hidden = !canEdit;
}

function renderAttachments(attachments) {
  document.getElementById("task-attachments").innerHTML = attachments.length ? attachments.map((attachment) => `
    <div class="attachment-row"><span>${iconSvg("file")}</span><span class="team-person"><strong>${escapeHtml(attachment.file_name)}</strong><small>${(attachment.file_size / 1024).toFixed(1)} KB · ${escapeHtml(attachment.user_full_name || attachment.user_email || "Tài khoản")}</small></span>
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
      const ok = await showConfirmModal({
        eyebrow: "TỆP ĐÍNH KÈM",
        title: "Xoá tệp đính kèm?",
        message: "Tệp đính kèm này sẽ bị xoá vĩnh viễn khỏi công việc.",
        confirmText: "Xoá tệp",
        danger: true,
      });
      if (!ok) return;
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

document.getElementById("checklist-form").querySelector('[name="content"]').addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    document.getElementById("checklist-form").querySelector("button").click();
  }
});

document.getElementById("comment-form").querySelector('[name="content"]').addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    document.getElementById("comment-form").querySelector("button").click();
  }
});

document.getElementById("checklist-form").querySelector("button").addEventListener("click", async () => {
  const input = document.getElementById("checklist-form").querySelector('[name="content"]');
  const content = input.value.trim();
  if (!content) {
    setFieldError(input, "Vui lòng nhập nội dung mục checklist.");
    input.focus();
    return;
  }
  clearFieldError(input);
  if (!currentTask) return;
  try {
    await api.post(`/projects/${projectId}/tasks/${currentTask.id}/checklist`, { content });
    input.value = "";
    const data = await api.get(`/projects/${projectId}/tasks/${currentTask.id}/checklist/summary`);
    renderChecklist(data);
    scheduleSilentBoardSync(150);
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
    scheduleSilentBoardSync(150);
  } catch (error) {
    event.target.checked = !event.target.checked;
    showToast(error.message, "error");
  }
});

document.getElementById("checklist-items").addEventListener("click", async (event) => {
  const moveBtn = event.target.closest("[data-checklist-move]");
  if (moveBtn && currentTask) {
    const id = Number(moveBtn.dataset.checklistId);
    const dir = moveBtn.dataset.checklistMove;
    const ids = currentChecklistItems.map((i) => i.id);
    const idx = ids.indexOf(id);
    const targetIdx = dir === "up" ? idx - 1 : idx + 1;
    if (idx < 0 || targetIdx < 0 || targetIdx >= ids.length) return;
    [ids[idx], ids[targetIdx]] = [ids[targetIdx], ids[idx]];
    try {
      await api.patch(`/projects/${projectId}/tasks/${currentTask.id}/checklist/reorder`, { item_ids: ids });
      renderChecklist(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/checklist/summary`));
    } catch (error) {
      showToast(error.message, "error");
    }
    return;
  }

  const editBtn = event.target.closest("[data-checklist-edit]");
  if (editBtn && currentTask) {
    const itemId = Number(editBtn.dataset.checklistEdit);
    const item = currentChecklistItems.find((i) => i.id === itemId);
    if (!item) return;
    const content = await showPromptModal({
      eyebrow: "CHECKLIST",
      title: "Chỉnh sửa mục kiểm tra",
      label: "Nội dung mục checklist *",
      defaultValue: item.content,
      maxlength: 500,
      submitText: "Lưu thay đổi",
      requiredMessage: "Vui lòng nhập nội dung mục checklist.",
    });
    if (!content || content === item.content) return;
    try {
      await api.put(`/projects/${projectId}/tasks/${currentTask.id}/checklist/${itemId}`, { content });
      renderChecklist(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/checklist/summary`));
      showToast("Đã cập nhật mục checklist");
    } catch (error) {
      showToast(error.message, "error");
    }
    return;
  }

  const button = event.target.closest("[data-checklist-delete]");
  if (!button || !currentTask) return;
  const ok = await showConfirmModal({
    eyebrow: "CHECKLIST",
    title: "Xoá mục kiểm tra?",
    message: "Bạn có chắc chắn muốn xoá mục này khỏi danh sách kiểm tra?",
    confirmText: "Xoá mục",
    danger: true,
  });
  if (!ok) return;
  try {
    await api.delete(`/projects/${projectId}/tasks/${currentTask.id}/checklist/${button.dataset.checklistDelete}`);
    renderChecklist(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/checklist/summary`));
    scheduleSilentBoardSync(150);
  } catch (error) {
    showToast(error.message, "error");
  }
});

document.getElementById("task-comments").addEventListener("click", async (event) => {
  const editBtn = event.target.closest("[data-comment-edit]");
  if (editBtn && currentTask) {
    const commentId = Number(editBtn.dataset.commentEdit);
    const comment = currentComments.find((c) => c.id === commentId);
    if (!comment) return;
    const content = await showPromptModal({
      eyebrow: "BÌNH LUẬN",
      title: "Chỉnh sửa bình luận",
      label: "Nội dung bình luận *",
      defaultValue: comment.content,
      maxlength: 5000,
      submitText: "Lưu bình luận",
      requiredMessage: "Vui lòng nhập nội dung bình luận.",
    });
    if (!content || content === comment.content) return;
    try {
      await api.put(`/projects/${projectId}/tasks/${currentTask.id}/comments/${commentId}`, { content });
      renderComments(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/comments`));
      showToast("Đã cập nhật bình luận");
    } catch (error) {
      showToast(error.message, "error");
    }
    return;
  }

  const deleteBtn = event.target.closest("[data-comment-delete]");
  if (deleteBtn && currentTask) {
    const commentId = Number(deleteBtn.dataset.commentDelete);
    const ok = await showConfirmModal({
      eyebrow: "BÌNH LUẬN",
      title: "Xoá bình luận này?",
      message: "Bình luận sẽ bị xoá khỏi công việc và không thể khôi phục.",
      confirmText: "Xoá bình luận",
      danger: true,
    });
    if (!ok) return;
    try {
      await api.delete(`/projects/${projectId}/tasks/${currentTask.id}/comments/${commentId}`);
      renderComments(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/comments`));
      scheduleSilentBoardSync(150);
      showToast("Đã xoá bình luận");
    } catch (error) {
      showToast(error.message, "error");
    }
  }
});

document.getElementById("comment-form").querySelector("button").addEventListener("click", async () => {
  const input = document.getElementById("comment-form").querySelector('[name="content"]');
  const content = input.value.trim();
  if (!content) {
    setFieldError(input, "Vui lòng nhập nội dung bình luận.");
    input.focus();
    return;
  }
  clearFieldError(input);
  if (!currentTask) return;
  try {
    await api.post(`/projects/${projectId}/tasks/${currentTask.id}/comments`, { content });
    input.value = "";
    renderComments(await api.get(`/projects/${projectId}/tasks/${currentTask.id}/comments`));
    scheduleSilentBoardSync(150);
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
    result.innerHTML = `<strong>Đã tạo lời mời cho ${escapeHtml(invitation.invitee_email)}.</strong><p>Hết hạn: ${escapeHtml(new Date(invitation.expires_at).toLocaleDateString("vi-VN"))}</p><input readonly value="${escapeHtml(inviteUrl)}"><button class="btn btn-small btn-primary" type="button" id="copy-invite-link">Sao chép liên kết</button><small>Chia sẻ liên kết này với người được mời hoặc bảo họ kiểm tra mục "Lời mời dự án".</small>`;
    result.hidden = false;
    document.getElementById("copy-invite-link").addEventListener("click", async () => {
      await navigator.clipboard.writeText(inviteUrl);
      showToast("Đã sao chép liên kết lời mời");
    });
    form.reset();
    await openTeamDialog();
  } catch (error) {
    if (!applyApiErrorsToForm(form, error)) {
      showToast(error.message, "error");
    }
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
    if (!member) return;
    const ok = await showConfirmModal({
      eyebrow: "CHUYỂN QUYỀN SỞ HỮU",
      title: "Chuyển quyền Owner dự án?",
      message: `Bạn sắp chuyển quyền Owner cho ${member.user?.full_name || member.user?.email}. Sau khi chuyển, vai trò của bạn sẽ trở thành Manager.`,
      confirmText: "Xác nhận chuyển Owner",
    });
    if (!ok) return;
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
  const ok = await showConfirmModal({
    eyebrow: "THÀNH VIÊN DỰ ÁN",
    title: "Xoá thành viên khỏi dự án?",
    message: "Thành viên này sẽ không còn quyền truy cập bảng công việc của dự án.",
    confirmText: "Xoá thành viên",
    danger: true,
  });
  if (!ok) return;
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
  activeTab = tab;
  const isActivity = tab === "activity";
  const isStats = tab === "stats";
  const isTable = tab === "table";
  const isBoard = tab === "board";

  document.querySelector(".board-toolbar").hidden = isActivity || isStats;
  boardElement.hidden = !isBoard;
  if (tablePanel) tablePanel.hidden = !isTable;
  const statsPanel = document.getElementById("stats-panel");
  if (statsPanel) statsPanel.hidden = !isStats;
  document.getElementById("activity-panel").hidden = !isActivity;

  document.querySelectorAll("[data-project-tab]").forEach((link) => {
    const active = link.dataset.projectTab === tab;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  if (isActivity) loadActivity();
  if (isStats) renderStatsView();
}

const ACTIVITY_ACTION_LABELS = {
  created: "đã tạo mới",
  updated: "đã cập nhật",
  moved: "đã di chuyển",
  deleted: "đã xoá",
  restored: "đã khôi phục",
  assigned: "đã giao việc",
  unassigned: "đã bỏ giao việc",
};

const ACTIVITY_ENTITY_LABELS = {
  task: "Công việc",
  comment: "Bình luận",
  attachment: "Tệp đính kèm",
  assignee: "Phân công",
  list: "Cột trạng thái",
  label: "Nhãn",
  project: "Dự án",
};

function activityLogRowMarkup(log) {
  const actionLabel = ACTIVITY_ACTION_LABELS[log.action] || log.action.replaceAll("_", " ");
  const entityLabel = ACTIVITY_ENTITY_LABELS[log.entity_type] || log.entity_type;
  const taskTag = log.task_id ? ` #${log.task_id}` : "";
  const detailBlocks = [];
  if (log.old_value) detailBlocks.push(`Trước: ${log.old_value}`);
  if (log.new_value) detailBlocks.push(`Sau: ${log.new_value}`);
  return `<article class="activity-row"><span class="activity-mark">${escapeHtml(initials(log.user_full_name || "U"))}</span>
    <div><strong>${escapeHtml(log.user_full_name || "Tài khoản")}</strong> <span>${escapeHtml(actionLabel)} · ${escapeHtml(entityLabel)}${escapeHtml(taskTag)}</span>
      <time>${escapeHtml(formatDateTime(log.created_at))}</time>
      ${detailBlocks.length ? `<details><summary>Xem dữ liệu thay đổi</summary><pre>${escapeHtml(detailBlocks.join("\n"))}</pre></details>` : ""}
    </div></article>`;
}

function populateActivityUserFilter() {
  if (!activityUserFilter) return;
  const current = activityUserFilter.value;
  activityUserFilter.innerHTML = `<option value="">Mọi thành viên</option>`
    + (members || []).map((m) => {
      const name = m.user?.full_name || m.user?.email || `Thành viên #${m.user_id}`;
      return `<option value="${m.user_id}" ${String(m.user_id) === current ? "selected" : ""}>${escapeHtml(name)}</option>`;
    }).join("");
}

async function loadActivity(page = 1) {
  const container = document.getElementById("activity-list");
  const pagination = document.getElementById("activity-pagination");
  const pageInfo = document.getElementById("activity-page-info");
  const prevBtn = document.getElementById("activity-prev-page");
  const nextBtn = document.getElementById("activity-next-page");
  populateActivityUserFilter();
  container.innerHTML = '<p class="muted">Đang tải nhật ký…</p>';
  try {
    const params = { page, size: ACTIVITY_PAGE_SIZE };
    if (activityUserFilter?.value) params.user_id = Number(activityUserFilter.value);
    if (activityActionFilter?.value) params.action = activityActionFilter.value;
    if (activityEntityFilter?.value) params.entity_type = activityEntityFilter.value;

    const response = await http.get(`/projects/${projectId}/activity-logs`, { params });
    const logs = response.data || [];
    const total = Number(response.headers?.["x-total-count"] ?? logs.length);
    activityPage = Number(response.headers?.["x-page"] ?? page) || 1;
    activityTotalPages = Math.max(1, Number(response.headers?.["x-total-pages"] ?? Math.ceil(total / ACTIVITY_PAGE_SIZE)) || 1);

    container.innerHTML = logs.length ? logs.map(activityLogRowMarkup).join("")
      : '<p class="empty-state">Không có hoạt động nào khớp bộ lọc.</p>';

    if (pagination) {
      pagination.hidden = total === 0;
      if (pageInfo) pageInfo.textContent = `Trang ${activityPage} / ${activityTotalPages} · Tổng ${total} hoạt động`;
      if (prevBtn) prevBtn.disabled = activityPage <= 1;
      if (nextBtn) nextBtn.disabled = activityPage >= activityTotalPages;
    }
  } catch (error) {
    container.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
    if (pagination) pagination.hidden = true;
  }
}

activityUserFilter?.addEventListener("change", () => loadActivity(1));
activityActionFilter?.addEventListener("change", () => loadActivity(1));
activityEntityFilter?.addEventListener("change", () => loadActivity(1));
document.getElementById("activity-prev-page")?.addEventListener("click", () => {
  if (activityPage > 1) loadActivity(activityPage - 1);
});
document.getElementById("activity-next-page")?.addEventListener("click", () => {
  if (activityPage < activityTotalPages) loadActivity(activityPage + 1);
});

document.querySelector(".tabs").addEventListener("click", (event) => {
  const link = event.target.closest("[data-project-tab]");
  if (!link) return;
  event.preventDefault();
  if (link.dataset.projectTab === "members") {
    openTeamDialog();
    return;
  }
  setProjectTab(link.dataset.projectTab);
  window.history.replaceState({}, "", `${window.location.pathname}${window.location.search}#${link.dataset.projectTab}`);
});

tableBody?.addEventListener("click", (event) => {
  const row = event.target.closest("[data-table-task-id]");
  if (row) openTask(Number(row.dataset.tableTaskId));
});

async function handleListAction(action, listId) {
  const list = boardData.lists.find((item) => item.id === listId);
  if (!list) return;
  try {
    if (action === "rename") {
      const name = await showPromptModal({
        eyebrow: "CỘT TRẠNG THÁI KANBAN",
        title: "Đổi tên cột công việc",
        description: "Nhập tên mới cho cột trạng thái trên bảng Kanban của dự án.",
        label: "Tên cột trạng thái *",
        defaultValue: list.name,
        placeholder: "VD: Cần làm, Đang triển khai, Kiểm thử…",
        maxlength: 100,
        submitText: "Lưu tên cột",
        requiredMessage: "Vui lòng nhập tên cột trạng thái.",
      });
      if (!name || name === list.name) return;
      await api.put(`/projects/${projectId}/lists/${listId}`, { name });
      showToast(`Đã đổi tên cột thành "${name}"`);
    } else if (action === "done") {
      const nextDone = !list.is_done_column;
      await api.put(`/projects/${projectId}/lists/${listId}`, { is_done_column: nextDone });
      showToast(nextDone ? `Đã đặt "${list.name}" làm cột Hoàn thành` : `Đã bỏ đánh dấu cột Hoàn thành cho "${list.name}"`);
    } else if (action === "delete") {
      const otherLists = boardData.lists.filter((item) => item.id !== listId);
      if (!otherLists.length) return showToast("Dự án phải còn ít nhất một danh sách", "error");
      if (list.is_done_column) return showToast("Không thể xoá cột hoàn thành duy nhất", "error");
      const hasTasks = boardData.tasks.some((task) => task.list_id === listId);
      const { confirmed, targetListId } = await showDeleteListModal(list, otherLists, hasTasks);
      if (!confirmed) return;
      if (hasTasks && targetListId) {
        await api.delete(`/projects/${projectId}/lists/${listId}?target_list_id=${targetListId}`);
      } else {
        await api.delete(`/projects/${projectId}/lists/${listId}`);
      }
      showToast(`Đã xoá cột "${list.name}"`);
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
    if (!projectLabels.length) projectLabels = await api.get(`/projects/${projectId}/labels`);
    return openTaskForm(Number(addTask.dataset.createTask));
  }
  if (event.target.closest("#add-list-button")) {
    const name = await showPromptModal({
      eyebrow: "CỘT TRẠNG THÁI KANBAN",
      title: "Thêm cột trạng thái mới",
      description: "Tạo cột mới để phân chia giai đoạn xử lý công việc trên bảng Kanban.",
      label: "Tên cột trạng thái *",
      placeholder: "VD: Đang kiểm thử (QA), Chờ nghiệm thu…",
      maxlength: 100,
      submitText: "＋ Tạo cột mới",
      requiredMessage: "Vui lòng nhập tên cột trạng thái mới.",
    });
    if (!name) return;
    try {
      await api.post(`/projects/${projectId}/lists`, { name });
      showToast(`Đã thêm cột "${name}"`);
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
let activeDropColumn = null;
let canStartColumnDrag = false;
let columnDropSide = "before"; // "before" | "after"

function updateColumnDragEligibility(event) {
  canStartColumnDrag = Boolean(
    canManageLists
    && event.target.closest("[data-list-drag-handle]")
    && !event.target.closest(".column-actions, button, .task-card"),
  );
}

boardElement.addEventListener("pointerdown", updateColumnDragEligibility);
boardElement.addEventListener("mousedown", updateColumnDragEligibility);

function clearDropTargetHighlight() {
  if (activeDropColumn) {
    activeDropColumn.classList.remove("drop-target", "drop-column-before", "drop-column-after");
    activeDropColumn = null;
  }
  boardElement.querySelectorAll(".drop-target, .drop-column-before, .drop-column-after").forEach((el) => {
    el.classList.remove("drop-target", "drop-column-before", "drop-column-after");
  });
}

boardElement.addEventListener("dragstart", (event) => {
  const task = event.target.closest(".task-card");
  const column = event.target.closest(".board-column");
  if (task && canEdit) {
    canStartColumnDrag = false;
    draggedListId = null;
    draggedTask = boardData.tasks.find((item) => item.id === Number(task.dataset.taskId));
    event.dataTransfer.setData("text/task-id", String(task.dataset.taskId));
    event.dataTransfer.effectAllowed = "move";
    requestAnimationFrame(() => task.classList.add("dragging"));
  } else if (column && canManageLists && canStartColumnDrag) {
    draggedTask = null;
    draggedListId = Number(column.dataset.listId);
    event.dataTransfer.setData("text/list-id", String(draggedListId));
    event.dataTransfer.effectAllowed = "move";
    requestAnimationFrame(() => column.classList.add("dragging-column"));
  } else {
    event.preventDefault();
  }
});

boardElement.addEventListener("dragend", () => {
  boardElement.querySelectorAll(".dragging, .dragging-column").forEach((element) => {
    element.classList.remove("dragging", "dragging-column");
  });
  clearDropTargetHighlight();
  draggedTask = null;
  draggedListId = null;
  canStartColumnDrag = false;
});

boardElement.addEventListener("dragover", (event) => {
  const column = event.target.closest(".board-column");
  if (!column) return;

  if (draggedTask && canEdit) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    if (activeDropColumn !== column) {
      clearDropTargetHighlight();
      column.classList.add("drop-target");
      activeDropColumn = column;
    }
    return;
  }

  if (draggedListId && canManageLists) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    if (Number(column.dataset.listId) === draggedListId) {
      clearDropTargetHighlight();
      return;
    }
    const rect = column.getBoundingClientRect();
    const nextSide = event.clientX < rect.left + rect.width / 2 ? "before" : "after";
    if (activeDropColumn !== column || columnDropSide !== nextSide) {
      clearDropTargetHighlight();
      columnDropSide = nextSide;
      column.classList.add(nextSide === "before" ? "drop-column-before" : "drop-column-after");
      activeDropColumn = column;
    }
  }
});

boardElement.addEventListener("dragleave", (event) => {
  if (!boardElement.contains(event.relatedTarget)) {
    clearDropTargetHighlight();
  }
});

boardElement.addEventListener("drop", async (event) => {
  const column = event.target.closest(".board-column");
  clearDropTargetHighlight();
  if (!column) return;
  event.preventDefault();

  if (draggedTask && canEdit) {
    const task = draggedTask;
    draggedTask = null;
    const targetListId = Number(column.dataset.listId);
    if (task.list_id === targetListId) return;

    const prevListId = task.list_id;
    const prevPosition = task.position;
    const prevCompletedAt = task.completed_at;

    const targetList = boardData.lists.find((l) => l.id === targetListId);
    const siblings = boardData.tasks.filter((item) => item.list_id === targetListId && item.id !== task.id);

    // Cập nhật giao diện tức thì (Optimistic UI) — không gọi renderLoading() để tránh nháy trang
    task.list_id = targetListId;
    task.position = siblings.length;
    if (targetList?.is_done_column) {
      task.completed_at = task.completed_at || new Date().toISOString();
    } else {
      task.completed_at = null;
    }
    renderBoard();

    try {
      const updated = await api.patch(`/projects/${projectId}/tasks/${task.id}/move`, {
        list_id: targetListId,
        position: task.position,
      });
      if (updated) {
        Object.assign(task, updated);
        renderInsights();
        renderTableView(getFilteredTasks());
        renderStatsView();
        broadcastLocalBoardEvent("task_moved", updated);
      }
    } catch (error) {
      // Hoàn tác nếu lỗi mạng hoặc phân quyền
      task.list_id = prevListId;
      task.position = prevPosition;
      task.completed_at = prevCompletedAt;
      renderBoard();
      showToast(error.message, "error");
    }
    return;
  }

  if (draggedListId && canManageLists) {
    const movingListId = draggedListId;
    const dropSide = columnDropSide;
    draggedListId = null;
    canStartColumnDrag = false;
    const targetColId = Number(column.dataset.listId);
    if (!targetColId || movingListId === targetColId) return;

    boardData.lists.sort((a, b) => a.position - b.position || a.id - b.id);
    const previous = boardData.lists.map((item) => ({ ...item }));
    const from = boardData.lists.findIndex((list) => list.id === movingListId);
    if (from < 0) return;

    const [movingList] = boardData.lists.splice(from, 1);
    const targetIdxAfterRemove = boardData.lists.findIndex((list) => list.id === targetColId);
    if (targetIdxAfterRemove < 0) {
      boardData.lists = previous;
      return;
    }

    const insertIdx = dropSide === "after" ? targetIdxAfterRemove + 1 : targetIdxAfterRemove;
    boardData.lists.splice(insertIdx, 0, movingList);
    boardData.lists.forEach((item, index) => { item.position = index; });
    renderBoard();

    try {
      const reordered = await api.patch(`/projects/${projectId}/lists/reorder`, {
        list_ids: boardData.lists.map((item) => item.id),
      });
      if (Array.isArray(reordered)) {
        boardData.lists = reordered;
        renderBoard();
      }
      broadcastLocalBoardEvent("list_reordered", boardData.lists);
    } catch (error) {
      boardData.lists = previous;
      renderBoard();
      showToast(error.message, "error");
    }
  }
});

newTaskButton.addEventListener("click", async () => {
  if (!members.length) members = await api.get(`/projects/${projectId}/members`);
  if (!projectLabels.length) projectLabels = await api.get(`/projects/${projectId}/labels`);
  openTaskForm(boardData.lists[0]?.id);
});
retryButton.addEventListener("click", loadBoard);
searchInput.addEventListener("input", renderBoard);
priorityFilter.addEventListener("change", renderBoard);
assigneeFilter?.addEventListener("change", renderBoard);
labelFilter?.addEventListener("change", renderBoard);
document.querySelector(".header-search input")?.addEventListener("input", (event) => {
  searchInput.value = event.target.value;
  renderBoard();
});

let projectSocket = null;
let projectSocketId = null;
let projectPingTimer = null;
let projectReconnectTimer = null;
let silentSyncTimer = null;
const boardBroadcastChannel = typeof BroadcastChannel !== "undefined"
  ? new BroadcastChannel("agile-project-board-sync")
  : null;

function broadcastLocalBoardEvent(event, data) {
  if (!boardBroadcastChannel || !projectId) return;
  try {
    boardBroadcastChannel.postMessage({ projectId, event, data });
  } catch {}
}

if (boardBroadcastChannel) {
  boardBroadcastChannel.addEventListener("message", (msg) => {
    const payload = msg.data;
    if (!payload || Number(payload.projectId) !== Number(projectId)) return;
    handleProjectRealtimeMessage({ event: payload.event, data: payload.data });
  });
}

async function syncBoardSilently() {
  if (!projectId || draggedTask || draggedListId) return;
  try {
    const board = await api.get(`/projects/${projectId}/board`);
    if (draggedTask || draggedListId) return;
    boardData = board;
    renderBoard();
  } catch {}
}

function scheduleSilentBoardSync(delayMs = 180) {
  clearTimeout(silentSyncTimer);
  silentSyncTimer = setTimeout(syncBoardSilently, delayMs);
}

function handleProjectRealtimeMessage(payload) {
  if (!payload || !boardData) return;
  const { event, data } = payload;

  if ((event === "task_moved" || event === "task_updated" || event === "task_created") && data && data.id) {
    if (!draggedTask) {
      const idx = boardData.tasks.findIndex((t) => t.id === data.id);
      if (idx >= 0) {
        const oldListId = boardData.tasks[idx].list_id;
        Object.assign(boardData.tasks[idx], data);
        // Sắp xếp lại vị trí các thẻ cùng cột để phản ánh vị trí mới ngay lập tức
        const siblings = boardData.tasks
          .filter((t) => t.list_id === data.list_id && t.id !== data.id)
          .sort((a, b) => a.position - b.position || a.id - b.id);
        const targetPos = Math.max(0, Math.min(Number(data.position) || 0, siblings.length));
        siblings.splice(targetPos, 0, boardData.tasks[idx]);
        siblings.forEach((t, i) => { t.position = i; });
        if (oldListId !== data.list_id) {
          boardData.tasks
            .filter((t) => t.list_id === oldListId)
            .sort((a, b) => a.position - b.position || a.id - b.id)
            .forEach((t, i) => { t.position = i; });
        }
      } else {
        boardData.tasks.push(data);
      }
      renderBoard();
    }
    scheduleSilentBoardSync(220);
    return;
  }

  if (event === "task_deleted" && data && data.task_id) {
    boardData.tasks = boardData.tasks.filter((t) => t.id !== Number(data.task_id));
    renderBoard();
    scheduleSilentBoardSync(200);
    return;
  }

  if (event === "list_reordered" && Array.isArray(data)) {
    if (!draggedListId) {
      boardData.lists = data;
      renderBoard();
    }
    return;
  }

  if (
    event === "task_restored"
    || event === "task_reordered"
    || event === "list_created"
    || event === "list_updated"
    || event === "list_deleted"
  ) {
    scheduleSilentBoardSync(80);
    return;
  }

  if (
    (event === "comment_added" || event === "comment_updated" || event === "comment_deleted" || event === "checklist_updated")
    && taskDialog.open
    && currentTask
    && Number(data?.task_id) === Number(currentTask.id)
  ) {
    loadTaskExtras(currentTask.id);
  }
}

function connectProjectWebSocket(targetProjectId) {
  const token = localStorage.getItem("access_token") || localStorage.getItem("token");
  if (!token || !targetProjectId) return;
  if (
    projectSocket
    && projectSocketId === targetProjectId
    && (projectSocket.readyState === WebSocket.OPEN || projectSocket.readyState === WebSocket.CONNECTING)
  ) {
    return;
  }

  if (projectSocket) {
    try { projectSocket.close(); } catch {}
    projectSocket = null;
  }

  projectSocketId = targetProjectId;
  const wsBase = CONFIG.API_BASE_URL.replace(/^http/i, "ws");
  const wsUrl = `${wsBase}/ws/projects/${targetProjectId}?token=${encodeURIComponent(token)}`;

  try {
    projectSocket = new WebSocket(wsUrl);
  } catch {
    return;
  }

  projectSocket.addEventListener("open", () => {
    clearInterval(projectPingTimer);
    projectPingTimer = setInterval(() => {
      if (projectSocket && projectSocket.readyState === WebSocket.OPEN) {
        projectSocket.send("ping");
      }
    }, 20000);
  });

  projectSocket.addEventListener("message", (event) => {
    try {
      const payload = JSON.parse(event.data);
      handleProjectRealtimeMessage(payload);
    } catch {}
  });

  projectSocket.addEventListener("close", (event) => {
    clearInterval(projectPingTimer);
    projectSocket = null;
    const stillLoggedIn = Boolean(localStorage.getItem("access_token") || localStorage.getItem("token"));
    if (stillLoggedIn && event.code !== 1008 && projectId === targetProjectId) {
      clearTimeout(projectReconnectTimer);
      projectReconnectTimer = setTimeout(() => connectProjectWebSocket(targetProjectId), 3000);
    }
  });
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && projectId && !taskDialog.open) {
    loadBoard();
    connectProjectWebSocket(projectId);
  }
});
loadBoard();
