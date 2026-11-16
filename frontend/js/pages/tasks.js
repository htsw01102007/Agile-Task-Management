// Trang Board: hiển thị các cột (lists) và task trong mỗi cột.
//   Xem task        -> GET    /lists/{id}/tasks    (member trở lên)
//   Thêm nhanh      -> POST   /lists/{id}/tasks    (manager trở lên)
//   Sửa tiêu đề     -> PATCH  /tasks/{id}          (manager trở lên)
//   Xoá (có confirm)-> DELETE /tasks/{id}          (manager trở lên)
//   Gán người       -> PUT    /tasks/{id}/assignees (manager trở lên)
//   Bỏ gán          -> DELETE /tasks/{id}/assignees/{uid}
//   Việc của tôi    -> GET    /my-tasks

const PROJECT_ID = 1;
const userIdInput = document.getElementById("user-id");
const board = document.getElementById("board");

let listsCache = []; // các cột đang hiển thị

function headers() {
  return { "X-User-Id": Number(userIdInput.value || 10) };
}

// ---------- Tải dữ liệu ----------
async function loadBoard() {
  board.innerHTML = "<p>Đang tải...</p>";
  try {
    listsCache = await api.get(
      `/projects/${PROJECT_ID}/lists`,
      undefined,
      headers()
    );
    // Tải song song task của từng cột
    const tasksPerList = await Promise.all(
      listsCache.map((l) =>
        api.get(`/lists/${l.id}/tasks`, undefined, headers())
      )
    );
    // Tải assignee cho mọi task rồi mới vẽ (để avatar hiện ngay từ đầu)
    await loadAssignees(tasksPerList.flat().map((t) => t.id));
    renderBoard(tasksPerList);
  } catch (error) {
    board.innerHTML = `<p class="text-error">${error.message}</p>`;
  }
}

function renderBoard(tasksPerList) {
  board.innerHTML = "";
  listsCache.forEach((list, i) => {
    const column = document.createElement("section");
    column.className = "column";
    column.dataset.listId = list.id;
    const doneBadge = list.is_done_column
      ? '<span class="done-badge">✅ hoàn thành</span>'
      : "";
    column.innerHTML = `
      <h3>${escapeHtml(list.name)} ${doneBadge}</h3>
      <div class="tasks"></div>
      <form class="quick-add">
        <input name="title" placeholder="+ Thêm task nhanh" autocomplete="off" />
      </form>`;
    const container = column.querySelector(".tasks");
    tasksPerList[i].forEach((task) => container.appendChild(renderCard(task)));
    board.appendChild(column);
  });
}

// Cache avatar/tên của assignee theo task để vẽ trên thẻ
const assigneesCache = {}; // taskId -> [{user_id, full_name, avatar_url}]

async function loadAssignees(taskIds) {
  await Promise.all(
    taskIds.map(async (id) => {
      try {
        assigneesCache[id] = await api.get(
          `/tasks/${id}/assignees`,
          undefined,
          headers()
        );
      } catch {
        assigneesCache[id] = [];
      }
    })
  );
}

function avatarHtml(userId, fullName, avatarUrl) {
  const initial = (fullName || `#${userId}`).trim().charAt(0).toUpperCase();
  if (avatarUrl) {
    return `<img class="avatar" src="${escapeHtml(
      avatarUrl
    )}" alt="${escapeHtml(fullName || "")}" title="${escapeHtml(
      fullName || ""
    )}" />`;
  }
  // Không có ảnh -> avatar chữ cái đầu
  return `<span class="avatar avatar-letter" title="${escapeHtml(
    fullName || ""
  )}">${escapeHtml(initial)}</span>`;
}

function renderCard(task) {
  const card = document.createElement("div");
  card.className = "task-card";
  card.dataset.taskId = task.id;
  const due = task.due_date
    ? ` · hết hạn ${formatDateTime(task.due_date)}`
    : "";
  // Avatar người thực hiện (đã tải trước bằng loadAssignees)
  const assignees = (assigneesCache[task.id] || [])
    .map((a) => avatarHtml(a.user_id, a.full_name, a.avatar_url))
    .join("");
  card.innerHTML = `
    <div class="task-title" title="Bấm để sửa tiêu đề">${escapeHtml(
      task.title
    )}</div>
    <div class="task-meta">${task.priority}${due}</div>
    <div class="card-footer">
      <button class="btn btn-small" data-action="assign">👤 Người thực hiện</button>
      <span class="assignees">${assignees}</span>
      <button class="btn btn-small btn-danger" data-action="delete">Xoá</button>
    </div>`;
  return card;
}

// ---------- Thêm nhanh task cuối cột ----------
board.addEventListener("submit", async (event) => {
  if (!event.target.matches(".quick-add")) return;
  event.preventDefault();
  const input = event.target.title;
  const title = input.value.trim();
  if (!title) return;
  const listId = event.target.closest(".column").dataset.listId;
  try {
    await api.post(`/lists/${listId}/tasks`, { title }, headers());
    loadBoard();
  } catch (error) {
    alert(error.message); // 403 nếu không phải manager+
  }
});

// ---------- Sửa tiêu đề trên thẻ ----------
board.addEventListener("dblclick", (event) => {
  const titleEl = event.target.closest(".task-title");
  if (!titleEl) return;
  const card = titleEl.closest(".task-card");
  titleEl.contentEditable = "true";
  titleEl.focus();
  // Chọn hết chữ cho dễ gõ đè
  const range = document.createRange();
  range.selectNodeContents(titleEl);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);

  const save = async () => {
    titleEl.contentEditable = "false";
    const newTitle = titleEl.textContent.trim();
    const oldTitle = titleEl.dataset.original || "";
    if (!newTitle || newTitle === oldTitle) return;
    try {
      await api.patch(
        `/tasks/${card.dataset.taskId}`,
        { title: newTitle },
        headers()
      );
    } catch (error) {
      alert(error.message);
      titleEl.textContent = oldTitle;
    }
  };
  titleEl.dataset.original = titleEl.textContent;
  titleEl.addEventListener("blur", save, { once: true });
  titleEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      titleEl.blur();
    }
  });
});

// Ghi nhớ tiêu đề gốc khi bắt đầu sửa
board.addEventListener("focusin", (event) => {
  const titleEl = event.target.closest(".task-title");
  if (titleEl && titleEl.contentEditable === "true") {
    titleEl.dataset.original ||= titleEl.textContent;
  }
});

// ---------- Xoá task có xác nhận ----------
board.addEventListener("click", async (event) => {
  const button = event.target.closest('button[data-action="delete"]');
  if (!button || button.disabled) return;
  button.disabled = true; // tránh double-click tạo confirm chồng nhau
  const card = button.closest(".task-card");
  if (
    !confirm(`Xoá task "${card.querySelector(".task-title").textContent}"?`)
  ) {
    button.disabled = false;
    return;
  }
  try {
    await api.delete(`/tasks/${card.dataset.taskId}`, headers());
    card.remove(); // xoá khỏi màn hình ngay (DB chỉ đánh dấu deleted_at)
  } catch (error) {
    alert(error.message);
    button.disabled = false;
  }
});

// ---------- Modal chọn người thực hiện ----------
// Modal đơn giản dựng bằng DOM; danh sách thành viên dự án lấy từ
// GET /projects/{pid}/lists không có -> dùng endpoint members khi có.
// Hiện tại: hardcode theo seed (id + tên); nhóm khác thay bằng GET /members.
const PROJECT_MEMBERS = [
  { user_id: 9, full_name: "An (owner)" },
  { user_id: 10, full_name: "Bình (manager)" },
  { user_id: 11, full_name: "Chi (member)" },
  { user_id: 12, full_name: "Dũng (viewer)" },
];

async function openAssignModal(taskId) {
  const current = assigneesCache[taskId] || [];
  const currentIds = current.map((a) => a.user_id);
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal">
      <h3>Người thực hiện — task #${taskId}</h3>
      <div class="member-list">
        ${PROJECT_MEMBERS.map(
          (m) => `
          <label>
            <input type="checkbox" value="${m.user_id}"
              ${currentIds.includes(m.user_id) ? "checked" : ""} />
            ${avatarHtml(m.user_id, m.full_name)} ${escapeHtml(m.full_name)}
          </label>`
        ).join("")}
      </div>
      <div class="modal-actions">
        <button class="btn" data-close>Huỷ</button>
        <button class="btn btn-primary" data-save>Lưu</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);

  overlay.querySelector("[data-close]").onclick = () => overlay.remove();
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.remove();
  });
  overlay.querySelector("[data-save]").onclick = async () => {
    const picked = [...overlay.querySelectorAll("input:checked")].map((i) =>
      Number(i.value)
    );
    try {
      // Gán thêm người mới
      for (const uid of picked.filter((id) => !currentIds.includes(id))) {
        await api.put(
          `/tasks/${taskId}/assignees`,
          { user_id: uid },
          headers()
        );
      }
      // Bỏ gán người bị bỏ chọn
      for (const uid of currentIds.filter((id) => !picked.includes(id))) {
        await api.delete(`/tasks/${taskId}/assignees/${uid}`, headers());
      }
      overlay.remove();
      loadBoard();
    } catch (error) {
      alert(error.message); // 422: không phải thành viên dự án / 409: đã gán
    }
  };
}

board.addEventListener("click", (event) => {
  const btn = event.target.closest('button[data-action="assign"]');
  if (!btn) return;
  openAssignModal(Number(btn.closest(".task-card").dataset.taskId));
});

// ---------- Lọc + tìm + phân trang (dạng danh sách) ----------
const filterForm = document.getElementById("filter-form");
const resultsDiv = document.getElementById("search-results");
const paginationDiv = document.getElementById("pagination");
let currentPage = 1;

// Đổ danh sách người thực hiện vào select lọc
async function loadAssigneeOptions() {
  const sel = document.getElementById("f-assignee");
  for (const m of PROJECT_MEMBERS) {
    const opt = document.createElement("option");
    opt.value = m.user_id;
    opt.textContent = m.full_name;
    sel.appendChild(opt);
  }
}

function readFilters() {
  const params = new URLSearchParams();
  const q = document.getElementById("f-q").value.trim();
  const pr = document.getElementById("f-priority").value;
  const st = document.getElementById("f-status").value;
  const as = document.getElementById("f-assignee").value;
  const da = document.getElementById("f-due-after").value;
  const db = document.getElementById("f-due-before").value;
  if (q) params.set("q", q);
  if (pr) params.set("priority", pr);
  if (st) params.set("task_status", st);
  if (as) params.set("assignee_id", as);
  if (da) params.set("due_after", `${da}T00:00:00`);
  if (db) params.set("due_before", `${db}T23:59:59`);
  params.set("page", currentPage);
  params.set("page_size", 10);
  return params;
}

async function runSearch() {
  resultsDiv.innerHTML = "<p>Đang tìm...</p>";
  paginationDiv.innerHTML = "";
  try {
    const data = await api.get(
      `/projects/${PROJECT_ID}/tasks/search?${readFilters()}`,
      undefined,
      headers()
    );
    renderResults(data);
  } catch (error) {
    resultsDiv.innerHTML = `<p class="text-error">${error.message}</p>`;
  }
}

function renderResults(data) {
  if (data.total === 0) {
    resultsDiv.innerHTML = `<p class="muted">Không có task nào khớp</p>`;
    return;
  }
  resultsDiv.innerHTML = data.items
    .map((t) => {
      const avatars = (assigneesCache[t.id] || [])
        .map((a) => avatarHtml(a.user_id, a.full_name, a.avatar_url))
        .join("");
      return `
      <div class="result-row">
        <span class="badge-${t.priority}">${t.priority}</span>
        <strong>${escapeHtml(t.title)}</strong>
        ${
          t.list_name
            ? `<span class="muted">· ${escapeHtml(t.list_name)}</span>`
            : ""
        }
        ${
          t.due_date
            ? `<span class="muted">· hết hạn ${formatDateTime(
                t.due_date
              )}</span>`
            : ""
        }
        ${t.completed_at ? "<span>✅</span>" : ""}
        <span class="assignees">${avatars}</span>
      </div>`;
    })
    .join("");

  // Phân trang
  let html = "";
  for (let p = 1; p <= data.total_pages; p++) {
    html += `<button data-page="${p}" class="${
      p === data.page ? "current" : ""
    }" ${p === data.page ? "disabled" : ""}>${p}</button>`;
  }
  paginationDiv.innerHTML = html;
}

filterForm.addEventListener("submit", (event) => {
  event.preventDefault();
  currentPage = 1;
  runSearch();
});

document.getElementById("f-reset").addEventListener("click", () => {
  filterForm.reset();
  currentPage = 1;
  resultsDiv.innerHTML = "";
  paginationDiv.innerHTML = "";
});

paginationDiv.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-page]");
  if (!button) return;
  currentPage = Number(button.dataset.page);
  runSearch();
});

loadAssigneeOptions();
userIdInput.addEventListener("change", loadBoard);
loadBoard();
