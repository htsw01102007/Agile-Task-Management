const invitationList = document.getElementById("my-invitations");

async function loadMyInvitations() {
  try {
    const invitations = await api.get("/invitations/me");
    invitationList.innerHTML = invitations.length ? invitations.map((invitation) => `
      <article class="my-task-row" data-invitation-id="${invitation.id}"><span class="task-status-dot ${invitation.status === "accepted" ? "done" : ""}"></span>
        <span class="my-task-main"><strong>Dự án #${invitation.project_id}</strong><small>${escapeHtml(invitation.invitee_email)} · Vai trò ${escapeHtml(invitation.role)}</small></span>
        <span class="role-badge">${escapeHtml(invitation.status)}</span>
        ${invitation.status === "pending" ? `
          <button class="btn btn-small btn-primary" type="button" data-invitation-action="accept" data-invitation-token="${escapeHtml(invitation.token)}">Chấp nhận</button>
          <button class="btn btn-small btn-danger" type="button" data-invitation-action="decline" data-invitation-token="${escapeHtml(invitation.token)}">Từ chối</button>
        ` : ""}
      </article>`).join("") : '<p class="empty-state">Bạn chưa nhận lời mời nào.</p>';
  } catch (error) {
    invitationList.innerHTML = `<p class="status status-error">${escapeHtml(error.message)}</p>`;
  }
}

invitationList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-invitation-action]");
  if (!button || button.disabled) return;

  const row = button.closest("[data-invitation-id]");
  const { invitationAction: action, invitationToken: token } = button.dataset;
  if (!row || !token || !["accept", "decline"].includes(action)) return;

  row.querySelectorAll("[data-invitation-action]").forEach((actionButton) => {
    actionButton.disabled = true;
  });

  try {
    const result = await api.post(`/invitations/${action}/${encodeURIComponent(token)}`);
    showToast(result.message);
    await loadMyInvitations();
  } catch (error) {
    showToast(error.message, "error");
    row.querySelectorAll("[data-invitation-action]").forEach((actionButton) => {
      actionButton.disabled = false;
    });
  }
});

loadMyInvitations();
