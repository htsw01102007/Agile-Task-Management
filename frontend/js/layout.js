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
    ? `<button class="header-auth" type="button" id="logout-button" title="Đăng xuất khỏi phiên làm việc">${iconSvg("logout")}<span>Đăng xuất</span></button>`
    : isLoginPage
      ? `<a class="header-auth" href="${root}index.html">Trang chủ</a>`
      : `<a class="header-auth" href="${root}pages/login.html">Đăng nhập</a>`;
  const projectId = new URLSearchParams(window.location.search).get("project");
  const isBoard = path.endsWith("project.html");
  const projectLinks = projects.map((project) => `
    <a class="nav-i project-link ${String(project.id) === projectId && isBoard ? "current" : ""}" href="${root}pages/project.html?project=${project.id}" title="${escapeHtml(project.name)}">
      <span class="ic project-icon">${escapeHtml(layoutInitials(project.name))}</span>
      <span class="lbl">${escapeHtml(project.name)}</span>
      ${typeof project.task_count === "number" ? `<span class="nav-count">${project.task_count}</span>` : ""}
    </a>`).join("") || `<p class="sidebar-empty">${escapeHtml(projectsMessage)}</p>`;

  const userLinks = isAuthenticated ? `
    <a class="nav-i ${path.endsWith("my-tasks.html") ? "current" : ""}" href="${root}pages/my-tasks.html"><span class="ic">${iconSvg("tasks")}</span><span class="lbl">Việc của tôi</span></a>
    <a class="nav-i ${path.endsWith("invitations.html") ? "current" : ""}" href="${root}pages/invitations.html"><span class="ic">${iconSvg("mail")}</span><span class="lbl">Lời mời dự án</span></a>
    <a class="nav-i ${path.endsWith("profile.html") ? "current" : ""}" href="${root}pages/profile.html"><span class="ic">${iconSvg("user")}</span><span class="lbl">Hồ sơ &amp; Bảo mật</span></a>` : "";

  const adminLinks = isAuthenticated && user.system_role === "admin" ? `
    <div class="sidebar-section admin-section"><p class="grp">QUẢN TRỊ HỆ THỐNG</p>
      <a class="nav-i ${path.endsWith("admin-users.html") ? "current" : ""}" href="${root}pages/admin-users.html"><span class="ic">${iconSvg("shield")}</span><span class="lbl">Quản lý người dùng</span></a>
    </div>` : "";

  const notifMarkup = isAuthenticated ? `
    <div class="notif-wrap">
      <button class="icon-btn notif-btn" type="button" id="notif-bell-btn" aria-label="Thông báo" title="Thông báo">
        ${iconSvg("bell")}<span id="notif-badge" class="notif-badge" hidden>0</span>
      </button>
      <div id="notif-dropdown" class="notif-dropdown" hidden>
        <div class="notif-header">
          <strong>Trung tâm thông báo</strong>
          <button class="btn btn-small" type="button" id="notif-read-all">Đánh dấu đã đọc</button>
        </div>
        <div id="notif-list" class="notif-list"><p class="muted notif-empty">Đang tải…</p></div>
      </div>
    </div>` : "";

  document.getElementById("app-header").innerHTML = `
    <button class="icon-btn sidebar-toggle" type="button" aria-label="Thu gọn thanh bên" aria-expanded="true">${iconSvg("menu")}</button>
    <a href="${root}index.html" class="logo">
      <span class="mark">${iconSvg("logo")}</span>
      <span class="brand-name">Agile Workspace</span>
      <span class="brand-tag">PRO</span>
    </a>
    <div class="header-search">
      <span aria-hidden="true">${iconSvg("search")}</span>
      <input id="global-search-input" type="search" placeholder="Tìm nhanh dự án hoặc công việc…" aria-label="Tìm công việc">
      <span class="kbd-hint">/</span>
    </div>
    <div class="grow"></div>
    <div class="header-right">
      ${notifMarkup}
      ${authAction}
      ${userAvatarMarkup(user, "avatar")}
    </div>`;

  document.getElementById("app-sidebar").innerHTML = `
    <div class="workspace-pill">
      <span class="workspace-pill-dot"></span>
      <div class="workspace-pill-info">
        <strong>Không gian Agile</strong>
        <small>${isAuthenticated ? (user.system_role === "admin" ? "Quản trị viên hệ thống" : "Thành viên chính thức") : "Chế độ khách"}</small>
      </div>
    </div>
    <div class="sidebar-section">
      <p class="grp">ĐIỀU HƯỚNG CHÍNH</p>
      <a class="nav-i ${path.endsWith("index.html") || path === "/" ? "current" : ""}" href="${root}index.html"><span class="ic">${iconSvg("home")}</span><span class="lbl">Tổng quan</span></a>
      ${userLinks}
    </div>
    <div class="sidebar-section project-section">
      <div class="section-heading">
        <p class="grp">DỰ ÁN (${projects.length})</p>
        ${isAuthenticated ? `<a class="small-icon icon-btn" href="${root}index.html#new-project" title="Tạo dự án mới" aria-label="Tạo dự án">${iconSvg("plus")}</a>` : ""}
      </div>
      ${projectLinks}
    </div>
    ${adminLinks}
    <a class="sidebar-bottom" href="${isAuthenticated ? `${root}pages/profile.html` : `${root}pages/login.html`}">
      ${userAvatarMarkup(user, "avatar avatar-small")}
      <span class="lbl">${escapeHtml(user.full_name || "Tài khoản")}<small class="sidebar-email">${escapeHtml(user.email || "Nhấn để đăng nhập")}</small></span>
    </a>`;

  hydrateIcons(document);

  document.querySelector(".sidebar-toggle").addEventListener("click", () => {
    const collapsed = app.classList.toggle("collapsed");
    document.querySelector(".sidebar-toggle").setAttribute("aria-expanded", String(!collapsed));
  });
  document.getElementById("logout-button")?.addEventListener("click", () => {
    ["access_token", "refresh_token", "token"].forEach((key) => localStorage.removeItem(key));
    window.location.href = `${root}index.html`;
  });

  const bellBtn = document.getElementById("notif-bell-btn");
  const dropdown = document.getElementById("notif-dropdown");
  if (bellBtn && dropdown) {
    bellBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      dropdown.hidden = !dropdown.hidden;
      if (!dropdown.hidden) await refreshNotifications(root);
    });
    document.getElementById("notif-read-all")?.addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await api.patch("/notifications/read-all");
        await refreshNotifications(root);
      } catch (err) {
        showToast(err.message, "error");
      }
    });
    document.addEventListener("click", (e) => {
      if (!dropdown.hidden && !e.target.closest(".notif-wrap")) {
        dropdown.hidden = true;
      }
    });
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)) {
    const searchEl = document.getElementById("global-search-input");
    if (searchEl) {
      e.preventDefault();
      searchEl.focus();
    }
  }
});

async function refreshNotifications(root = document.body.dataset.root || "./") {
  const badge = document.getElementById("notif-badge");
  const listEl = document.getElementById("notif-list");
  if (!badge || !listEl) return;
  try {
    const bell = await api.get("/notifications/bell", { limit: 15 });
    if (bell.unread_count > 0) {
      badge.textContent = bell.unread_count > 99 ? "99+" : String(bell.unread_count);
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
    if (!bell.items || !bell.items.length) {
      listEl.innerHTML = '<p class="muted notif-empty">Chưa có thông báo nào.</p>';
      return;
    }
    listEl.innerHTML = bell.items.map((n) => `
      <div class="notif-item ${n.is_read ? "" : "unread"}" data-notif-id="${n.id}" data-project-id="${n.project_id || ""}">
        <div class="notif-title">${escapeHtml(n.title)}</div>
        ${n.message ? `<div class="notif-msg">${escapeHtml(n.message)}</div>` : ""}
        <time class="notif-time">${escapeHtml(formatDateTime(n.created_at))}</time>
      </div>
    `).join("");
    listEl.querySelectorAll(".notif-item").forEach((item) => {
      item.addEventListener("click", async () => {
        const nid = item.dataset.notifId;
        const pid = item.dataset.projectId;
        try {
          await api.patch(`/notifications/${nid}/read`);
        } catch {}
        if (pid) {
          window.location.href = `${root}pages/project.html?project=${pid}`;
        } else {
          await refreshNotifications(root);
        }
      });
    });
  } catch {}
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
      refreshNotifications();
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
