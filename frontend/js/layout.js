const FALLBACK_USER = { full_name: "Khách", avatar_url: null, system_role: "user" };

function layoutInitials(name = "?") {
  return name.trim().split(/\s+/).slice(-2).map((part) => part[0]).join("").toUpperCase();
}

function userAvatarMarkup(user, className = "avatar") {
  const name = user.full_name || "Tài khoản";
  return user.avatar_url
    ? `<img class="${className} avatar-image" src="${escapeHtml(user.avatar_url)}" alt="${escapeHtml(name)}">`
    : `<span class="${className}">${escapeHtml(layoutInitials(name))}</span>`;
}

function renderLayout(projects = [], user = FALLBACK_USER, projectsMessage = "Chưa có dự án") {
  const app = document.getElementById("app");
  if (!app) return;
  const root = document.body.dataset.root || "./";
  const path = window.location.pathname;
  const isAuthenticated = Boolean(localStorage.getItem("access_token") || localStorage.getItem("token"));
  const isLoginPage = path.endsWith("login.html");
  const authAction = isAuthenticated
    ? '<button class="header-auth" type="button" id="logout-button">Đăng xuất</button>'
    : isLoginPage
      ? `<a class="header-auth" href="${root}index.html">Trang chủ</a>`
      : `<a class="header-auth" href="${root}pages/login.html?next=${encodeURIComponent(path + window.location.search)}">Đăng nhập</a>`;
  const projectId = new URLSearchParams(window.location.search).get("project");
  const isBoard = path.endsWith("project.html");
  const projectLinks = projects.map((project) => `
    <a class="nav-i project-link ${String(project.id) === projectId && isBoard ? "current" : ""}" href="${root}pages/project.html?project=${project.id}" title="${escapeHtml(project.name)}">
      <span class="ic project-icon">${escapeHtml(layoutInitials(project.name))}</span><span class="lbl">${escapeHtml(project.name)}</span>
    </a>`).join("") || `<p class="sidebar-empty">${escapeHtml(projectsMessage)}</p>`;
  const userLinks = isAuthenticated ? `
    <a class="nav-i ${path.endsWith("my-tasks.html") ? "current" : ""}" href="${root}pages/my-tasks.html"><span class="ic">✓</span><span class="lbl">Việc của tôi</span></a>
    <a class="nav-i ${path.endsWith("invitations.html") ? "current" : ""}" href="${root}pages/invitations.html"><span class="ic">✉</span><span class="lbl">Lời mời</span></a>
    <a class="nav-i ${path.endsWith("profile.html") ? "current" : ""}" href="${root}pages/profile.html"><span class="ic">◉</span><span class="lbl">Hồ sơ</span></a>` : "";
  const adminLinks = isAuthenticated && user.system_role === "admin" ? `
    <div class="sidebar-section admin-section"><p class="grp">QUẢN TRỊ</p>
      <a class="nav-i ${path.endsWith("admin-users.html") ? "current" : ""}" href="${root}pages/admin-users.html"><span class="ic">♙</span><span class="lbl">Người dùng</span></a>
    </div>` : "";

  document.getElementById("app-header").innerHTML = `
    <button class="icon-btn sidebar-toggle" type="button" aria-label="Thu gọn thanh bên" aria-expanded="true">☰</button>
    <a href="${root}index.html" class="logo"><span class="mark">A</span><span class="brand-name">Agile Workspace</span></a>
    <div class="header-search"><span aria-hidden="true">⌕</span><input type="search" placeholder="Tìm công việc" aria-label="Tìm công việc"></div>
    <div class="grow"></div>${authAction}${userAvatarMarkup(user, "avatar")}`;
  document.getElementById("app-sidebar").innerHTML = `
    <div class="sidebar-section"><p class="grp">KHÔNG GIAN LÀM VIỆC</p>
      <a class="nav-i ${path.endsWith("index.html") || path === "/" ? "current" : ""}" href="${root}index.html"><span class="ic">⌂</span><span class="lbl">Tổng quan</span></a>
      ${userLinks}
    </div>
    <div class="sidebar-section project-section"><div class="section-heading"><p class="grp">DỰ ÁN</p>${isAuthenticated ? `<a class="small-icon icon-btn" href="${root}index.html#new-project" aria-label="Tạo dự án">＋</a>` : ""}</div>${projectLinks}</div>
    ${adminLinks}
    <a class="sidebar-bottom" href="${isAuthenticated ? `${root}pages/profile.html` : "#"}">${userAvatarMarkup(user, "avatar avatar-small")}<span class="lbl">${escapeHtml(user.full_name || "Tài khoản")}<small class="sidebar-email">${escapeHtml(user.email || "")}</small></span></a>`;

  document.querySelector(".sidebar-toggle").addEventListener("click", () => {
    const collapsed = app.classList.toggle("collapsed");
    document.querySelector(".sidebar-toggle").setAttribute("aria-expanded", String(!collapsed));
  });
  document.getElementById("logout-button")?.addEventListener("click", () => {
    ["access_token", "refresh_token", "token"].forEach((key) => localStorage.removeItem(key));
    window.location.href = `${root}index.html`;
  });
}

async function loadLayoutData() {
  const isAuthenticated = Boolean(localStorage.getItem("access_token") || localStorage.getItem("token"));
  if (!isAuthenticated) {
    renderLayout();
    return;
  }
  try {
    const user = await api.get("/auth/me");
    renderLayout([], user, "Đang tải dự án…");
    window.dispatchEvent(new CustomEvent("layout:user-loaded", { detail: user }));
    try {
      const projects = await api.get("/projects/summary");
      renderLayout(projects, user);
    } catch (error) {
      if (error.status === 401 || error.status === 403) throw error;
      renderLayout([], user, "Không tải được dự án");
      showToast(error.message, "error");
    }
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      ["access_token", "refresh_token", "token"].forEach((key) => localStorage.removeItem(key));
      renderLayout([], FALLBACK_USER, error.status === 403 ? "Tài khoản đã bị khóa" : "Phiên đăng nhập đã hết hạn");
      window.dispatchEvent(new CustomEvent("auth:expired"));
      return;
    }
    renderLayout([], FALLBACK_USER, error.status === 0 ? "Không kết nối được backend" : "Không tải được dự án");
    showToast(error.message, "error");
  }
}

window.addEventListener("auth:expired", () => {
  if (window.location.pathname.endsWith("login.html")) return;
  const root = document.body.dataset.root || "./";
  const next = window.location.pathname + window.location.search;
  window.location.assign(`${root}pages/login.html?next=${encodeURIComponent(next)}`);
});

renderLayout();
loadLayoutData();
