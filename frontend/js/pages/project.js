const PROJECT_NAMES = {
  website: { name: "Website công ty", initial: "W", color: "teal", description: "Làm mới trải nghiệm website doanh nghiệp." },
  mobile: { name: "Ứng dụng di động", initial: "M", color: "amber", description: "Ứng dụng quản lý công việc cho nhóm." },
  marketing: { name: "Chiến dịch marketing", initial: "M", color: "violet", description: "Lên kế hoạch nội dung và ra mắt sản phẩm." },
};
const activeProject = PROJECT_NAMES[new URLSearchParams(window.location.search).get("project")] || PROJECT_NAMES.website;
document.title = `${activeProject.name} | Agile Workspace`;
document.getElementById("project-title").textContent = activeProject.name;
document.getElementById("project-crumb").textContent = activeProject.name;
document.querySelector(".project-description").textContent = activeProject.description;
document.querySelector(".project-title-row .project-mark").textContent = activeProject.initial;
document.querySelector(".project-title-row .project-mark").className = `project-mark ${activeProject.color}`;
