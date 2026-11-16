// Trang Lists: CRUD cột công việc trong project.
//   Xem           -> GET    /projects/{pid}/lists          (member trở lên)
//   Thêm          -> POST   /projects/{pid}/lists          (manager trở lên)
//   Sửa           -> PUT    /projects/{pid}/lists/{id}     (manager trở lên)
//   Đổi thứ tự    -> PUT    /projects/{pid}/lists/reorder  (manager trở lên)
//   Xoá           -> DELETE /projects/{pid}/lists/{id}     (manager trở lên)
// userId lấy từ ô input trên trang (thay bằng token thật khi có login).

const PROJECT_ID = 1;
const BASE = `/projects/${PROJECT_ID}/lists`;

const form = document.getElementById("list-form");
const tableBody = document.getElementById("list-table-body");
const userIdInput = document.getElementById("user-id");
const formTitle = document.getElementById("form-title");
const submitButton = document.getElementById("btn-submit");
const cancelButton = document.getElementById("btn-cancel");

let editingId = null; // null = đang thêm mới; có số = đang sửa

function headers() {
  return { "X-User-Id": Number(userIdInput.value || 1) };
}

function showError(error) {
  alert(error.message || "Có lỗi xảy ra"); // 403 -> "Cần vai trò manager trở lên..."
}

// ---------- Đọc dữ liệu ----------
async function loadLists() {
  tableBody.innerHTML = `<tr><td colspan="5" class="muted">Đang tải...</td></tr>`;
  try {
    const lists = await api.get(BASE, undefined, headers());
    renderLists(lists);
  } catch (error) {
    tableBody.innerHTML = `<tr><td colspan="5" class="text-error">${error.message}</td></tr>`;
  }
}

function renderLists(lists) {
  if (lists.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="5" class="muted">Chưa có cột nào</td></tr>`;
    return;
  }
  tableBody.innerHTML = lists
    .map(
      (item, index) => `
    <tr data-id="${item.id}">
      <td>${index + 1}</td>
      <td><strong>${escapeHtml(item.name)}</strong></td>
      <td>${item.position}</td>
      <td>${item.is_done_column ? "✅ Hoàn thành" : "—"}</td>
      <td class="actions">
        <button class="btn btn-small" data-action="up" ${
          index === 0 ? "disabled" : ""
        }>↑</button>
        <button class="btn btn-small" data-action="down"
          ${index === lists.length - 1 ? "disabled" : ""}>↓</button>
        <button class="btn btn-small" data-action="toggle-done">
          ${
            item.is_done_column ? "Bỏ hoàn thành" : "Đánh dấu hoàn thành"
          }</button>
        <button class="btn btn-small" data-action="edit">Sửa</button>
        <button class="btn btn-small btn-danger" data-action="delete">Xoá</button>
      </td>
    </tr>`
    )
    .join("");
}

// ---------- Thêm / Sửa ----------
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = {
    name: form.name.value.trim(),
    is_done_column: form.is_done_column.checked,
  };
  try {
    if (editingId) {
      await api.put(`${BASE}/${editingId}`, data, headers());
    } else {
      await api.post(BASE, data, headers());
    }
    resetForm();
    loadLists();
  } catch (error) {
    showError(error);
  }
});

function resetForm() {
  editingId = null;
  form.reset();
  formTitle.textContent = "Thêm cột mới";
  submitButton.textContent = "Thêm";
  cancelButton.hidden = true;
}

cancelButton.addEventListener("click", resetForm);

// ---------- Hành động trong bảng ----------
tableBody.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const row = button.closest("tr");
  const id = Number(row.dataset.id);

  // Gom id cột theo thứ tự hiện tại trên màn hình để gửi lên /reorder
  const currentIds = [...tableBody.querySelectorAll("tr[data-id]")].map((tr) =>
    Number(tr.dataset.id)
  );

  try {
    switch (button.dataset.action) {
      case "up":
      case "down": {
        const index = currentIds.indexOf(id);
        const swapWith = button.dataset.action === "up" ? index - 1 : index + 1;
        [currentIds[index], currentIds[swapWith]] = [
          currentIds[swapWith],
          currentIds[index],
        ];
        await api.put(`${BASE}/reorder`, { ids: currentIds }, headers());
        break;
      }
      case "toggle-done": {
        // Đánh dấu / bỏ cột hoàn thành: dùng endpoint /done để đảm bảo
        // mỗi project chỉ có 1 cột hoàn thành
        const isDone = row.children[3].textContent.includes("✅");
        if (isDone) {
          await api.put(`${BASE}/${id}`, { is_done_column: false }, headers());
        } else {
          await api.put(`${BASE}/${id}/done`, {}, headers());
        }
        break;
      }
      case "edit": {
        editingId = id;
        form.name.value = row.querySelector("strong").textContent;
        form.is_done_column.checked =
          row.children[3].textContent.includes("✅");
        formTitle.textContent = `Sửa cột #${id}`;
        submitButton.textContent = "Lưu";
        cancelButton.hidden = false;
        return;
      }
      case "delete": {
        // Hỏi trước số task sẽ bị xoá: đếm task của cột qua API tasks
        let taskCount = 0;
        try {
          const tasks = await api.get(
            `/lists/${id}/tasks`,
            undefined,
            headers()
          );
          taskCount = tasks.length;
        } catch {
          /* không đếm được thì vẫn cho xoá */
        }
        const msg =
          taskCount > 0
            ? `Xoá cột này? Sẽ xoá mềm ${taskCount} task trong cột.`
            : "Xoá cột này?";
        if (!confirm(msg)) return;
        await api.delete(`${BASE}/${id}`, headers());
        break;
      }
    }
    loadLists();
  } catch (error) {
    showError(error);
  }
});

// Đổi tên trực tiếp: dblclick vào tên cột đưa tên lên form
tableBody.addEventListener("dblclick", (event) => {
  const strong = event.target.closest("strong");
  if (!strong) return;
  const row = strong.closest("tr");
  editingId = Number(row.dataset.id);
  form.name.value = strong.textContent;
  form.is_done_column.checked = row.children[3].textContent.includes("✅");
  formTitle.textContent = `Đổi tên cột #${editingId}`;
  submitButton.textContent = "Lưu";
  cancelButton.hidden = false;
  form.name.focus();
});

loadLists();
