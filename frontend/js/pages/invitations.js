const invitationList = document.getElementById("my-invitations");

function statusBadgeClass(status) {
  if (status === "accepted") return "status-active";
  if (status === "pending") return "status-pending";
  return "status-inactive";
}

function statusLabel(status) {
  return { pending: "Đang chờ phản hồi", accepted: "Đã chấp nhận", declined: "Đã từ chối", cancelled: "Đã huỷ" }[status] || status;
}

async function loadMyInvitations() {
  try {
    const invitations = await api.get("/invitations/me");
    const pendingCount = invitations.filter((i) => i.status === "pending").length;
    const acceptedCount = invitations.filter((i) => i.status === "accepted").length;

    const totalEl = document.getElementById("inv-stat-total");
    const pendingEl = document.getElementById("inv-stat-pending");
    const acceptedEl = document.getElementById("inv-stat-accepted");
    if (totalEl) totalEl.textContent = invitations.length;
    if (pendingEl) pendingEl.textContent = pendingCount;
    if (acceptedEl) acceptedEl.textContent = acceptedCount;

    invitationList.innerHTML = invitations.length ? invitations.map((invitation) => `
      <article class="my-task-row">
        <span class="task-status-dot ${invitation.status === "accepted" ? "done" : ""}"></span>
        <span class="my-task-main">
          <strong>Lời mời tham gia Dự án #${invitation.project_id}</strong>
          <small>Email nhận: ${escapeHtml(invitation.invitee_email)} · Vai trò đề xuất: <b>${escapeHtml(invitation.role.toUpperCase())}</b> · Hết hạn: ${escapeHtml(formatDateTime(invitation.expires_at))}</small>
        </span>
        <span class="role-badge ${statusBadgeClass(invitation.status)}">${escapeHtml(statusLabel(invitation.status))}</span>
        ${invitation.status === "pending" ? `<span class="project-card-actions">
          <button class="btn btn-small btn-primary" type="button" data-accept-token="${escapeHtml(invitation.token)}">✓ Chấp nhận ngay</button>
          <button class="btn btn-small btn-danger" type="button" data-decline-token="${escapeHtml(invitation.token)}">Từ chối</button>
          <a class="btn btn-small" href="invitation.html?token=${encodeURIComponent(invitation.token)}">Chi tiết</a>
        </span>` : `<a class="btn btn-small" href="project.html?project=${invitation.project_id}">Mở dự án →</a>`}
      </article>`).join("") : '<p class="empty-state">Hiện tại bạn chưa nhận được lời mời tham gia dự án nào.</p>';
  } catch (error) {
    invitationList.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}

invitationList.addEventListener("click", async (e) => {
  const acceptBtn = e.target.closest("[data-accept-token]");
  const declineBtn = e.target.closest("[data-decline-token]");
  if (acceptBtn) {
    acceptBtn.disabled = true;
    try {
      const res = await api.post(`/invitations/accept/${encodeURIComponent(acceptBtn.dataset.acceptToken)}`);
      showToast(res.message || "Đã tham gia dự án!");
      window.location.assign(`project.html?project=${res.project_id}`);
    } catch (err) {
      showToast(err.message, "error");
      acceptBtn.disabled = false;
    }
  } else if (declineBtn) {
    const ok = await showConfirmModal({
      eyebrow: "LỜI MỜI DỰ ÁN",
      title: "Từ chối lời mời tham gia?",
      message: "Bạn có chắc chắn muốn từ chối lời mời tham gia dự án này không?",
      confirmText: "Từ chối lời mời",
      danger: true,
    });
    if (!ok) return;
    declineBtn.disabled = true;
    try {
      const res = await api.post(`/invitations/decline/${encodeURIComponent(declineBtn.dataset.declineToken)}`);
      showToast(res.message || "Đã từ chối lời mời.");
      await loadMyInvitations();
    } catch (err) {
      showToast(err.message, "error");
      declineBtn.disabled = false;
    }
  }
});

loadMyInvitations();
