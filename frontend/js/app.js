const app = document.getElementById("app");
const userBox = document.getElementById("user-box");
const state = {
  mode: "login",
  user: null,
  projects: [],
  board: null,
  selected: null,
  comments: [],
  error: "",
};

function esc(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function showError(error) {
  state.error = error?.message || "Có lỗi xảy ra";
  if (error?.status === 401) {
    localStorage.removeItem("token");
    state.user = null;
    state.board = null;
  }
  render();
}

async function apiCall(work) {
  state.error = "";
  try {
    return await work();
  } catch (error) {
    showError(error);
    return null;
  }
}

document.getElementById("brand").addEventListener("click", () => {
  state.board = null;
  state.selected = null;
  if (state.user) loadProjects();
  else render();
});

function consumeOAuthResult() {
  if (!location.hash) return;
  const params = new URLSearchParams(location.hash.slice(1));
  const token = params.get("token");
  const error = params.get("error");
  if (!token && !error) return;
  history.replaceState(null, "", location.pathname + location.search);
  if (token) localStorage.setItem("token", token);
  if (error) state.error = error;
}

async function boot() {
  consumeOAuthResult();
  if (!localStorage.getItem("token")) {
    render();
    return;
  }
  const user = await apiCall(() => api.get("/auth/me"));
  if (!user) return;
  state.user = user;
  await loadProjects();
}

async function loadProjects() {
  const projects = await apiCall(() => api.get("/projects"));
  if (!projects) return;
  state.projects = projects;
  state.board = null;
  state.selected = null;
  render();
}

async function openProject(id) {
  const board = await apiCall(() => api.get(`/projects/${id}/board`));
  if (!board) return;
  state.board = board;
  state.selected = null;
  state.comments = [];
  render();
}

async function openTask(task) {
  state.selected = task;
  const comments = await apiCall(() => api.get(`/tasks/${task.id}/comments`));
  state.comments = comments || [];
  render();
}

function renderUser() {
  if (!state.user) {
    userBox.innerHTML = "";
    return;
  }
  userBox.innerHTML = `<span>${esc(state.user.full_name)}</span><button id="logout" type="button">Đăng xuất</button>`;
  document.getElementById("logout").onclick = () => {
    localStorage.removeItem("token");
    state.user = null;
    state.board = null;
    render();
  };
}

function renderAuth() {
  const login = state.mode === "login";
  app.innerHTML = `
    <section class="panel">
      <div class="tabs">
        <button type="button" class="${login ? "active" : ""}" data-mode="login">Đăng nhập</button>
        <button type="button" class="${login ? "" : "active"}" data-mode="register">Đăng ký</button>
      </div>
      <form id="auth-form">
        ${login ? "" : `<label>Họ tên</label><input name="full_name" required>
        <label>Tên đăng nhập</label><input name="username" required minlength="3">`}
        <label>Email</label><input name="email" type="email" required>
        <label>Mật khẩu</label><input name="password" type="password" required>
        <p class="muted">Mật khẩu đăng ký: 8–72 ký tự, có chữ hoa, chữ thường và số.</p>
        <p class="error">${esc(state.error)}</p>
        <button class="btn" type="submit">${login ? "Đăng nhập" : "Tạo tài khoản"}</button>
      </form>
      <div class="social">
        <button class="btn google" id="google-login" type="button">Continue with Google</button>
        <button class="btn facebook" id="facebook-login" type="button">Continue with Facebook</button>
      </div>
    </section>`;
  app.querySelectorAll("[data-mode]").forEach((button) => {
    button.onclick = () => {
      state.mode = button.dataset.mode;
      state.error = "";
      render();
    };
  });
  const startOAuth = (button, path) => {
    button.onclick = () => {
      button.disabled = true;
      button.textContent = "Đang chuyển...";
      window.location.href = `${CONFIG.API_BASE_URL}${path}`;
    };
  };
  startOAuth(app.querySelector("#google-login"), "/auth/google/login");
  startOAuth(app.querySelector("#facebook-login"), "/auth/facebook/login");
  app.querySelector("#auth-form").onsubmit = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    const path = login ? "/auth/login" : "/auth/register";
    const session = await apiCall(() => api.post(path, data));
    if (!session) return;
    localStorage.setItem("token", session.access_token);
    state.user = session.user;
    await loadProjects();
  };
}

function renderProjects() {
  app.innerHTML = `
    <div class="toolbar">
      <h1>Dự án của tôi</h1>
    </div>
    <form id="new-project" class="row">
      <input name="name" placeholder="Tên dự án mới" required>
      <button class="btn" type="submit">Tạo dự án</button>
    </form>
    <p class="error">${esc(state.error)}</p>
    <div class="project-grid">
      ${state.projects.map((project) => `
        <button class="project-card" data-id="${project.id}">
          <strong>${esc(project.name)}</strong>
          <div class="muted">${esc(project.status)} · ${esc(project.role)}</div>
          <p>${esc(project.description || "")}</p>
        </button>`).join("") || `<p class="muted">Chưa có dự án.</p>`}
    </div>`;
  app.querySelector("#new-project").onsubmit = async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    const created = await apiCall(() => api.post("/projects", data));
    if (created) openProject(created.id);
  };
  app.querySelectorAll(".project-card").forEach((button) => {
    button.onclick = () => openProject(button.dataset.id);
  });
}

function renderComments() {
  const items = state.comments.map((comment) => `
    <div class="comment">
      <strong>${esc(comment.author?.full_name || "Ẩn danh")}</strong>
      <div>${esc(comment.content)}</div>
      ${(comment.replies || []).map((reply) => `
        <div class="comment reply">
          <strong>${esc(reply.author?.full_name || "Ẩn danh")}</strong>
          <div>${esc(reply.content)}</div>
        </div>`).join("")}
    </div>`).join("");
  return items || `<p class="muted">Chưa có bình luận.</p>`;
}

function renderBoard() {
  const board = state.board;
  const writable = board.project.status === "active" && board.project.role !== "viewer";
  const task = state.selected;
  app.innerHTML = `
    <div class="toolbar">
      <div>
        <button class="btn secondary" id="back" type="button">Dự án</button>
        <h1>${esc(board.project.name)}</h1>
        <p class="muted">${esc(board.project.description || "")}</p>
      </div>
      ${writable ? `<form id="new-list" class="row"><input name="name" placeholder="Cột mới" required><button class="btn" type="submit">Thêm cột</button></form>` : ""}
    </div>
    <p class="error">${esc(state.error)}</p>
    <div class="board">
      ${board.lists.map((column) => `
        <section class="column">
          <h3>${esc(column.name)} (${column.tasks.length})</h3>
          ${column.tasks.map((item) => `
            <button class="task-card ${esc(item.priority)}" data-task="${item.id}" type="button">
              <strong>${esc(item.title)}</strong>
              <div class="muted">${esc(item.priority)}</div>
            </button>`).join("")}
          ${writable ? `<form class="add-inline" data-list="${column.id}"><input name="title" placeholder="Thêm việc" required><button class="btn" type="submit">+</button></form>` : ""}
        </section>`).join("")}
    </div>
    ${task ? `
      <section class="drawer">
        <h2>Chi tiết công việc</h2>
        <form id="task-form">
          <label>Tên</label><input name="title" value="${esc(task.title)}" ${writable ? "" : "disabled"} required>
          <label>Mô tả</label><textarea name="description" rows="3" ${writable ? "" : "disabled"}>${esc(task.description || "")}</textarea>
          <label>Ưu tiên</label>
          <select name="priority" ${writable ? "" : "disabled"}>
            ${["low", "medium", "high", "urgent"].map((item) => `<option value="${item}" ${item === task.priority ? "selected" : ""}>${item}</option>`).join("")}
          </select>
          <label>Chuyển cột</label>
          <select name="list_id" ${writable ? "" : "disabled"}>
            ${board.lists.map((column) => `<option value="${column.id}" ${column.id === task.list_id ? "selected" : ""}>${esc(column.name)}</option>`).join("")}
          </select>
          ${writable ? `<div class="row"><button class="btn" type="submit">Lưu</button><button class="btn danger" id="delete-task" type="button">Xoá</button></div>` : ""}
        </form>
        <h3>Bình luận</h3>
        ${renderComments()}
        ${writable ? `<form id="comment-form" class="row"><input name="content" placeholder="Viết bình luận" required><button class="btn" type="submit">Gửi</button></form>` : ""}
      </section>` : ""}`;

  app.querySelector("#back").onclick = () => loadProjects();
  const listForm = app.querySelector("#new-list");
  if (listForm) {
    listForm.onsubmit = async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(event.currentTarget));
      const created = await apiCall(() => api.post(`/projects/${board.project.id}/lists`, data));
      if (created) openProject(board.project.id);
    };
  }
  app.querySelectorAll(".add-inline").forEach((form) => {
    form.onsubmit = async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(form));
      data.list_id = Number(form.dataset.list);
      const created = await apiCall(() => api.post(`/projects/${board.project.id}/tasks`, data));
      if (created) openProject(board.project.id);
    };
  });
  app.querySelectorAll("[data-task]").forEach((button) => {
    button.onclick = () => {
      const id = Number(button.dataset.task);
      const found = board.lists.flatMap((column) => column.tasks).find((item) => item.id === id);
      if (found) openTask(found);
    };
  });
  const taskForm = app.querySelector("#task-form");
  if (taskForm && writable) {
    taskForm.onsubmit = async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(taskForm));
      data.list_id = Number(data.list_id);
      const saved = await apiCall(() => api.put(`/tasks/${task.id}`, data));
      if (saved) await openProject(board.project.id);
    };
    app.querySelector("#delete-task").onclick = async () => {
      const removed = await apiCall(() => api.delete(`/tasks/${task.id}`));
      if (removed !== null) openProject(board.project.id);
    };
  }
  const commentForm = app.querySelector("#comment-form");
  if (commentForm) {
    commentForm.onsubmit = async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(commentForm));
      const created = await apiCall(() => api.post(`/tasks/${task.id}/comments`, data));
      if (created) openTask(task);
    };
  }
}

function render() {
  renderUser();
  if (!state.user) renderAuth();
  else if (!state.board) renderProjects();
  else renderBoard();
}

boot();
