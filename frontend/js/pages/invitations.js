const invitationList = document.getElementById("my-invitations");

async function loadMyInvitations() {
  try {
    const invitations = await api.get("/invitations/me");
    invitationList.innerHTML = invitations.length ? invitations.map((invitation) => `
      <article class="my-task-row"><span class="task-status-dot ${invitation.status === "accepted" ? "done" : ""}"></span>
        <span class="my-task-main"><strong>Dự án #${invitation.project_id}</strong><small>${escapeHtml(invitation.invitee_email)} · Vai trò ${escapeHtml(invitation.role)}</small></span>
        <span class="role-badge">${escapeHtml(invitation.status)}</span>
        ${invitation.status === "pending" ? '<span class="muted">Mở liên kết do người mời gửi để phản hồi.</span>' : ""}
      </article>`).join("") : '<p class="empty-state">Bạn chưa nhận lời mời nào.</p>';
  } catch (error) {
    invitationList.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}

loadMyInvitations();
