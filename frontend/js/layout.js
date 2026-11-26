const FALLBACK_USER = { full_name: "Khách", avatar_url: null, system_role: "user" };
let cachedLayoutProjects = [];
let cachedLayoutUser = FALLBACK_USER;
let globalSearchTimer = null;
let activeSearchIndex = 0;

function updateActiveSearchItem(dropdown, newIndex, scroll = true) {
  if (!dropdown) return;
  const items = Array.from(dropdown.querySelectorAll("a.search-result-item"));
  if (!items.length) {
    activeSearchIndex = -1;
    return;
  }
  activeSearchIndex = ((newIndex % items.length) + items.length) % items.length;
  items.forEach((item, idx) => {
    const isActive = idx === activeSearchIndex;
    item.classList.toggle("active", isActive);
    item.setAttribute("aria-selected", String(isActive));
    if (isActive && scroll) {
      item.scrollIntoView({ block: "nearest" });
    }
  });
}

function layoutInitials(name = "?") {
  return name.trim().split(/\s+/).slice(-2).map((part) => part[0]).join("").toUpperCase();
}

function userAvatarMarkup(user, className = "avatar") {
  const name = user.full_name || "Tài khoản";
  return user.avatar_url
    ? `<img class="${className} avatar-image" src="${escapeHtml(user.avatar_url)}" alt="${escapeHtml(name)}">`
    : `<span class="${className}">${escapeHtml(layoutInitials(name))}</span>`;
}

function syncPageSearchFilter(query) {
  const path = window.location.pathname;
  if (path.endsWith("index.html") || path === "/" || path.endsWith("/frontend/")) {
    const projSearch = document.getElementById("project-search");
    if (projSearch && projSearch.value !== query) {
      projSearch.value = query;
      projSearch.dispatchEvent(new Event("input", { bubbles: true }));
    }
  } else if (path.endsWith("project.html")) {
    const taskSearch = document.getElementById("task-search");
    if (taskSearch && taskSearch.value !== query) {
      taskSearch.value = query;
      taskSearch.dispatchEvent(new Event("input", { bubbles: true }));
    }
  } else if (path.endsWith("my-tasks.html")) {
    const myTaskSearch = document.querySelector('#task-filters input[name="search"]');
    if (myTaskSearch) {
      myTaskSearch.value = query;
    }
  } else if (path.endsWith("admin-users.html")) {
    const userSearch = document.querySelector('#user-filters input[name="q"]');
    if (userSearch) {
      userSearch.value = query;
    }
  } else if (path.endsWith("items.html")) {
    const itemSearch = document.getElementById("search-input");
    if (itemSearch && itemSearch.value !== query) {
      itemSearch.value = query;
      itemSearch.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }
}

async function renderGlobalSearchDropdown(query, root) {
  const dropdown = document.getElementById("global-search-dropdown");
  if (!dropdown) return;

  const isAuthenticated = Boolean(localStorage.getItem("access_token") || localStorage.getItem("token"));
  const q = query.trim().toLocaleLowerCase("vi");

  // 1. Lọc dự án đã tải
  const matchedProjects = cachedLayoutProjects.filter((p) => {
    if (!q) return true;
    return p.name.toLocaleLowerCase("vi").includes(q)
      || (p.description || "").toLocaleLowerCase("vi").includes(q);
  }).slice(0, 5);

  // 2. Lọc công việc trên bảng Kanban hiện tại (nếu đang mở trang project.html) hoặc gọi API tìm task
  let matchedTasks = [];
  if (typeof boardData !== "undefined" && boardData && Array.isArray(boardData.tasks)) {
    matchedTasks = boardData.tasks.filter((t) => {
      if (!q) return true;
      return t.title.toLocaleLowerCase("vi").includes(q)
        || (t.description || "").toLocaleLowerCase("vi").includes(q)
        || `#${t.id}`.includes(q);
    }).slice(0, 6).map((t) => ({
      ...t,
      _localBoardTask: true,
    }));
  } else if (isAuthenticated && q.length >= 1) {
    try {
      const apiTasks = await api.get("/tasks/my-tasks", { search: query.trim(), page: 1, size: 6 });
      matchedTasks = Array.isArray(apiTasks) ? apiTasks : [];
    } catch {}
  }

  // 3. Các lối tắt điều hướng nhanh
  const navShortcuts = [
    { label: "Tổng quan Dashboard", desc: "Danh mục dự án và thống kê tiến độ", href: `${root}index.html`, icon: "home" },
    ...(isAuthenticated ? [
      { label: "Việc của tôi", desc: "Tất cả công việc được giao cho bạn", href: `${root}pages/my-tasks.html`, icon: "tasks" },
      { label: "Lời mời dự án", desc: "Xem và phản hồi lời mời tham gia dự án", href: `${root}pages/invitations.html`, icon: "mail" },
      { label: "Hồ sơ & Bảo mật", desc: "Cập nhật họ tên và đổi mật khẩu", href: `${root}pages/profile.html`, icon: "user" },
    ] : [
      { label: "Đăng nhập", desc: "Truy cập không gian làm việc của bạn", href: `${root}pages/login.html`, icon: "user" },
    ]),
    ...(isAuthenticated && cachedLayoutUser?.system_role === "admin" ? [
      { label: "Quản lý người dùng (Admin)", desc: "Danh bạ tài khoản và phân quyền hệ thống", href: `${root}pages/admin-users.html`, icon: "shield" },
    ] : []),
  ].filter((item) => !q || item.label.toLocaleLowerCase("vi").includes(q) || item.desc.toLocaleLowerCase("vi").includes(q));

  let html = "";

  if (matchedProjects.length) {
    html += `<div class="search-group-title">Dự án (${matchedProjects.length})</div>`;
    html += matchedProjects.map((p) => `
      <a class="search-result-item" href="${root}pages/project.html?project=${p.id}">
        <span class="search-result-icon">${escapeHtml(layoutInitials(p.name))}</span>
        <div class="search-result-body">
          <strong>${escapeHtml(p.name)}</strong>
          <small>${p.task_count || 0} công việc · Hoàn thành ${Math.round(p.completion_rate || 0)}%</small>
        </div>
        <span class="role-badge">${escapeHtml(p.user_role || "member")}</span>
      </a>
    `).join("");
  }

  if (matchedTasks.length) {
    const projectMap = new Map(cachedLayoutProjects.map((p) => [p.id, p]));
    html += `<div class="search-group-title">Công việc (${matchedTasks.length})</div>`;
    html += matchedTasks.map((t) => {
      const projName = projectMap.get(t.project_id)?.name || `Dự án #${t.project_id}`;
      return `
        <a class="search-result-item" href="${root}pages/project.html?project=${t.project_id}&task=${t.id}" data-search-task-id="${t._localBoardTask ? t.id : ""}">
          <span class="search-result-icon">#${t.id}</span>
          <div class="search-result-body">
            <strong>${escapeHtml(t.title)}</strong>
            <small>${escapeHtml(projName)}</small>
          </div>
          <span class="priority priority-${escapeHtml(t.priority || "medium")}">${escapeHtml(t.priority || "medium")}</span>
        </a>
      `;
    }).join("");
  }

  if (navShortcuts.length) {
    html += `<div class="search-group-title">Đi tới trang</div>`;
    html += navShortcuts.map((nav) => `
      <a class="search-result-item" href="${nav.href}">
        <span class="search-result-icon">${iconSvg(nav.icon)}</span>
        <div class="search-result-body">
          <strong>${escapeHtml(nav.label)}</strong>
          <small>${escapeHtml(nav.desc)}</small>
        </div>
      </a>
    `).join("");
  }

  if (!html) {
    html = `<div class="search-empty">Không tìm thấy dự án hoặc công việc nào khớp với "<b>${escapeHtml(query)}</b>".</div>`;
  } else {
    html += `<div class="search-footer-hint"><span><kbd>↑</kbd><kbd>↓</kbd> Di chuyển</span><span><kbd>Enter</kbd> Mở mục chọn</span><span><kbd>Esc</kbd> Đóng</span></div>`;
  }

  dropdown.innerHTML = html;
  dropdown.hidden = false;
  updateActiveSearchItem(dropdown, 0, false);

  // Đồng bộ chuột (hover) và bàn phím (mũi tên lên/xuống)
  const items = Array.from(dropdown.querySelectorAll("a.search-result-item"));
  items.forEach((item, idx) => {
    item.addEventListener("mouseenter", () => {
      updateActiveSearchItem(dropdown, idx, false);
    });
  });

  // Nếu đang ở trang project.html và bấm vào kết quả task thuộc bảng hiện tại thì mở thẳng popup task
  dropdown.querySelectorAll("[data-search-task-id]").forEach((el) => {
    const localTaskId = Number(el.dataset.searchTaskId);
    if (localTaskId && typeof openTask === "function") {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        dropdown.hidden = true;
        openTask(localTaskId);
      });
    }
  });
}

function renderLayout(projects = [], user = FALLBACK_USER, projectsMessage = "Chưa có dự án") {
  const app = document.getElementById("app");
  if (!app) return;
  cachedLayoutProjects = Array.isArray(projects) ? projects : [];
  cachedLayoutUser = user || FALLBACK_USER;

  // Giữ lại từ khóa và trạng thái focus nếu thanh tìm kiếm đang được gõ
  const prevInput = document.getElementById("global-search-input");
  const prevValue = prevInput ? prevInput.value : "";
  const wasFocused = prevInput && document.activeElement === prevInput;

  const root = document.body.dataset.root || "./";
  const path = window.location.pathname;
  const isAuthenticated = Boolean(localStorage.getItem("access_token") || localStorage.getItem("token"));
  const isLoginPage = path.endsWith("login.html");
  const authAction = isAuthenticated
    ? ""
    : isLoginPage
      ? `<a class="header-auth" href="${root}index.html">Trang chủ</a>`
      : `<a class="header-auth" href="${root}pages/login.html">Đăng nhập</a>`;
  const currentTheme = typeof getEffectiveTheme === "function" ? getEffectiveTheme() : "light";
  const userMenuMarkup = `
    <div class="user-menu-wrap">
      <button class="avatar-trigger" type="button" id="avatar-menu-btn" aria-haspopup="menu" aria-expanded="false" title="Tài khoản &amp; Giao diện">
        ${userAvatarMarkup(user, "avatar")}
      </button>
      <div id="user-menu-dropdown" class="user-menu-dropdown" role="menu" hidden>
        <div class="user-menu-head">
          ${userAvatarMarkup(user, "avatar avatar-small")}
          <div class="user-menu-identity">
            <strong>${escapeHtml(user.full_name || "Tài khoản")}</strong>
            <small>${escapeHtml(user.email || (isAuthenticated ? "Thành viên chính thức" : "Chế độ khách"))}</small>
          </div>
        </div>
        <div class="user-menu-divider"></div>
        ${isAuthenticated
          ? `<a class="user-menu-item" role="menuitem" href="${root}pages/profile.html">${iconSvg("user")}<span>Hồ sơ</span></a>`
          : `<a class="user-menu-item" role="menuitem" href="${root}pages/login.html">${iconSvg("user")}<span>Đăng nhập</span></a>`}
        <div class="user-menu-theme-row" role="group" aria-label="Chế độ giao diện Light / Dark">
          <span class="user-menu-theme-label">
            <span class="theme-current-icon">${iconSvg(currentTheme === "dark" ? "moon" : "sun")}</span>
            <span>Theme</span>
          </span>
          <div class="theme-switch-pills">
            <button type="button" class="theme-pill${currentTheme === "light" ? " is-active" : ""}" data-theme-choice="light" aria-pressed="${currentTheme === "light"}">${iconSvg("sun")}<span>Light</span></button>
            <button type="button" class="theme-pill${currentTheme === "dark" ? " is-active" : ""}" data-theme-choice="dark" aria-pressed="${currentTheme === "dark"}">${iconSvg("moon")}<span>Dark</span></button>
          </div>
        </div>
        ${isAuthenticated ? `
          <div class="user-menu-divider"></div>
          <button class="user-menu-item user-menu-danger" role="menuitem" type="button" id="logout-button">${iconSvg("logout")}<span>Đăng xuất</span></button>
        ` : ""}
      </div>
    </div>`;
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
    <div class="header-search" id="global-search-box">
      <span aria-hidden="true">${iconSvg("search")}</span>
      <input id="global-search-input" type="search" autocomplete="off" placeholder="Tìm nhanh dự án, công việc hoặc trang (nhấn /)…" aria-label="Tìm nhanh dự án hoặc công việc">
      <span class="kbd-hint">/</span>
      <div id="global-search-dropdown" class="search-dropdown" hidden></div>
    </div>
    <div class="grow"></div>
    <div class="header-right">
      ${notifMarkup}
      ${authAction}
      ${userMenuMarkup}
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

  const searchInput = document.getElementById("global-search-input");
  const searchDropdown = document.getElementById("global-search-dropdown");
  if (searchInput) {
    searchInput.value = prevValue;
    if (wasFocused) searchInput.focus();

    searchInput.addEventListener("focus", () => {
      renderGlobalSearchDropdown(searchInput.value, root);
    });

    searchInput.addEventListener("input", () => {
      const q = searchInput.value;
      syncPageSearchFilter(q);
      clearTimeout(globalSearchTimer);
      globalSearchTimer = setTimeout(() => {
        renderGlobalSearchDropdown(q, root);
      }, 150);
    });

    searchInput.addEventListener("keydown", async (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (searchDropdown && searchDropdown.hidden) {
          await renderGlobalSearchDropdown(searchInput.value, root);
        } else {
          updateActiveSearchItem(searchDropdown, activeSearchIndex + 1, true);
        }
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (searchDropdown && searchDropdown.hidden) {
          await renderGlobalSearchDropdown(searchInput.value, root);
        } else {
          updateActiveSearchItem(searchDropdown, activeSearchIndex - 1, true);
        }
      } else if (e.key === "Escape") {
        if (searchDropdown) searchDropdown.hidden = true;
        searchInput.blur();
      } else if (e.key === "Enter") {
        const activeLink =
          searchDropdown?.querySelector("a.search-result-item.active") ||
          searchDropdown?.querySelector("a.search-result-item");
        if (activeLink && !searchDropdown.hidden) {
          e.preventDefault();
          activeLink.click();
        }
      }
    });
  }

  document.querySelector(".sidebar-toggle").addEventListener("click", () => {
    const collapsed = app.classList.toggle("collapsed");
    document.querySelector(".sidebar-toggle").setAttribute("aria-expanded", String(!collapsed));
  });
  document.getElementById("logout-button")?.addEventListener("click", () => {
    ["access_token", "refresh_token", "token"].forEach((key) => localStorage.removeItem(key));
    window.location.href = `${root}index.html`;
  });

  const avatarBtn = document.getElementById("avatar-menu-btn");
  const userDropdown = document.getElementById("user-menu-dropdown");
  const bellBtn = document.getElementById("notif-bell-btn");
  const dropdown = document.getElementById("notif-dropdown");

  if (avatarBtn && userDropdown) {
    avatarBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const willOpen = userDropdown.hidden;
      if (dropdown && !dropdown.hidden) dropdown.hidden = true;
      userDropdown.hidden = !willOpen;
      avatarBtn.setAttribute("aria-expanded", String(willOpen));
    });
    userDropdown.querySelectorAll("[data-theme-choice]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (typeof setUserTheme === "function") {
          setUserTheme(btn.dataset.themeChoice);
        }
      });
    });
  }

  if (bellBtn && dropdown) {
    bellBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (userDropdown && !userDropdown.hidden) {
        userDropdown.hidden = true;
        avatarBtn?.setAttribute("aria-expanded", "false");
      }
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
  }
}

document.addEventListener("click", (e) => {
  const notifDropdown = document.getElementById("notif-dropdown");
  if (notifDropdown && !notifDropdown.hidden && !e.target.closest(".notif-wrap")) {
    notifDropdown.hidden = true;
  }
  const userDropdown = document.getElementById("user-menu-dropdown");
  if (userDropdown && !userDropdown.hidden && !e.target.closest(".user-menu-wrap")) {
    userDropdown.hidden = true;
    document.getElementById("avatar-menu-btn")?.setAttribute("aria-expanded", "false");
  }
  const searchDropdown = document.getElementById("global-search-dropdown");
  if (searchDropdown && !searchDropdown.hidden && !e.target.closest("#global-search-box")) {
    searchDropdown.hidden = true;
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const userDropdown = document.getElementById("user-menu-dropdown");
    if (userDropdown && !userDropdown.hidden) {
      userDropdown.hidden = true;
      document.getElementById("avatar-menu-btn")?.setAttribute("aria-expanded", "false");
    }
    const notifDropdown = document.getElementById("notif-dropdown");
    if (notifDropdown && !notifDropdown.hidden) {
      notifDropdown.hidden = true;
    }
  }
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
      <div class="notif-item ${n.is_read ? "" : "unread"}" data-notif-id="${n.id}" data-notif-type="${escapeHtml(n.type || "")}" data-entity-type="${escapeHtml(n.entity_type || "")}" data-project-id="${n.project_id || ""}">
        <div class="notif-title">${escapeHtml(n.title)}</div>
        ${n.message ? `<div class="notif-msg">${escapeHtml(n.message)}</div>` : ""}
        <time class="notif-time">${escapeHtml(formatDateTime(n.created_at))}</time>
      </div>
    `).join("");
    listEl.querySelectorAll(".notif-item").forEach((item) => {
      item.addEventListener("click", async () => {
        const nid = item.dataset.notifId;
        const pid = item.dataset.projectId;
        const ntype = item.dataset.notifType;
        try {
          await api.patch(`/notifications/${nid}/read`);
        } catch {}
        if (ntype === "invitation_sent") {
          window.location.href = `${root}pages/invitations.html`;
        } else if (pid) {
          window.location.href = `${root}pages/project.html?project=${pid}`;
        } else {
          await refreshNotifications(root);
        }
      });
    });
  } catch {}
}

let notifSocket = null;
let notifPingTimer = null;
let notifReconnectTimer = null;

function connectNotificationWebSocket() {
  const token = localStorage.getItem("access_token") || localStorage.getItem("token");
  if (!token) return;
  if (notifSocket && (notifSocket.readyState === WebSocket.OPEN || notifSocket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const wsBase = CONFIG.API_BASE_URL.replace(/^http/i, "ws");
  const wsUrl = `${wsBase}/ws/notifications?token=${encodeURIComponent(token)}`;

  try {
    notifSocket = new WebSocket(wsUrl);
  } catch {
    return;
  }

  notifSocket.addEventListener("open", () => {
    clearInterval(notifPingTimer);
    notifPingTimer = setInterval(() => {
      if (notifSocket && notifSocket.readyState === WebSocket.OPEN) {
        notifSocket.send("ping");
      }
    }, 20000);
  });

  notifSocket.addEventListener("message", async (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.event === "notification_created" || payload.event === "deadline_reminder") {
        await refreshNotifications();
        const title = payload.data?.title || "Bạn có thông báo mới";
        const message = payload.data?.message ? ` — ${payload.data.message}` : "";
        showToast(`${title}${message}`);
        window.dispatchEvent(new CustomEvent("realtime:notification", { detail: payload.data }));
      }
    } catch {}
  });

  notifSocket.addEventListener("close", (event) => {
    clearInterval(notifPingTimer);
    notifSocket = null;
    // Tự động kết nối lại sau 3 giây nếu vẫn đang đăng nhập và không phải bị đóng do token không hợp lệ (1008)
    const stillLoggedIn = Boolean(localStorage.getItem("access_token") || localStorage.getItem("token"));
    if (stillLoggedIn && event.code !== 1008) {
      clearTimeout(notifReconnectTimer);
      notifReconnectTimer = setTimeout(connectNotificationWebSocket, 3000);
    }
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
    connectNotificationWebSocket();
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
