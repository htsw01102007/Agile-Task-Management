// Shell chung cho các trang trong ứng dụng.
const PROJECTS = [
  { id: "website", name: "Website công ty", color: "#0f6e7c" },
  { id: "mobile", name: "Ứng dụng di động", color: "#8a5a00" },
  { id: "marketing", name: "Chiến dịch marketing", color: "#7652a3" },
];

function renderLayout() {
  if (!document.getElementById("app")) return;
  const root = document.body.dataset.root || "./";
  const currentPath = window.location.pathname;
  const selectedProject = new URLSearchParams(window.location.search).get("project") || "website";
  const isBoard = currentPath.endsWith("project.html");
  const projectLinks = PROJECTS.map((project) => `
    <a class="nav-i project-link ${project.id === selectedProject && isBoard ? "current" : ""}"
       href="${root}pages/project.html?project=${project.id}" title="${project.name}">
      <span class="ic" style="--project-color:${project.color}">${project.name.slice(0, 1)}</span>
      <span class="lbl">${project.name}</span>
    </a>`).join("");

  document.getElementById("app-header").innerHTML = `
    <button class="icon-btn sidebar-toggle" type="button" aria-label="Thu gọn thanh bên" aria-expanded="true">☰</button>
    <a href="${root}index.html" class="logo"><span class="mark">A</span><span class="brand-name">Agile Workspace</span></a>
    <div class="header-search"><span aria-hidden="true">⌕</span><input type="search" placeholder="Tìm kiếm" aria-label="Tìm kiếm"></div>
    <div class="grow"></div>
    <button class="icon-btn" type="button" aria-label="Trợ giúp">?</button>
    <button class="avatar" type="button" aria-label="Tài khoản của bạn">D</button>`;

  document.getElementById("app-sidebar").innerHTML = `
    <div class="sidebar-section">
      <p class="grp">KHÔNG GIAN LÀM VIỆC</p>
      <a class="nav-i ${currentPath.endsWith("index.html") ? "current" : ""}" href="${root}index.html"><span class="ic">⌂</span><span class="lbl">Tổng quan</span></a>
      <a class="nav-i ${currentPath.endsWith("items.html") ? "current" : ""}" href="${root}pages/items.html"><span class="ic">▤</span><span class="lbl">Items (CRUD mẫu)</span></a>
    </div>
    <div class="sidebar-section project-section">
      <div class="section-heading"><p class="grp">DỰ ÁN</p><button class="icon-btn small-icon" type="button" aria-label="Tạo dự án">＋</button></div>
      ${projectLinks}
    </div>
    <div class="sidebar-bottom"><span class="avatar avatar-small">D</span><span class="lbl">Dung Nguyễn</span><span class="muted lbl">Thành viên</span></div>`;

  document.querySelector(".sidebar-toggle").addEventListener("click", () => {
    const app = document.getElementById("app");
    const collapsed = app.classList.toggle("collapsed");
    document.querySelector(".sidebar-toggle").setAttribute("aria-expanded", String(!collapsed));
  });
}

renderLayout();
