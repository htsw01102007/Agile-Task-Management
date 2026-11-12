// Trang Board: hiển thị các cột (lists) và task trong mỗi cột.
//   Xem task        -> GET    /lists/{id}/tasks    (member trở lên)
//   Thêm nhanh      -> POST   /lists/{id}/tasks    (manager trở lên)
//   Sửa tiêu đề     -> PATCH  /tasks/{id}          (manager trở lên)
//   Xoá (có confirm)-> DELETE /tasks/{id}          (manager trở lên)

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

function renderCard(task) {
  const card = document.createElement("div");
  card.className = "task-card";
  card.dataset.taskId = task.id;
  const due = task.due_date
    ? ` · hết hạn ${formatDateTime(task.due_date)}`
    : "";
  card.innerHTML = `
    <div class="task-title" title="Bấm để sửa tiêu đề">${escapeHtml(
      task.title
    )}</div>
    <div class="task-meta">${task.priority}${due}</div>
    <button class="btn btn-small btn-danger" data-action="delete">Xoá</button>`;
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
  if (!button) return;
  const card = button.closest(".task-card");
  if (!confirm(`Xoá task "${card.querySelector(".task-title").textContent}"?`))
    return;
  try {
    await api.delete(`/tasks/${card.dataset.taskId}`, headers());
    card.remove(); // xoá khỏi màn hình ngay (DB chỉ đánh dấu deleted_at)
  } catch (error) {
    alert(error.message);
  }
});

userIdInput.addEventListener("change", loadBoard);
loadBoard();
