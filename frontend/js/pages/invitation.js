const invitationToken = new URLSearchParams(window.location.search).get("token");
const invitationMessage = document.getElementById("invitation-message");
const acceptButton = document.getElementById("accept-invitation");
const declineButton = document.getElementById("decline-invitation");

if (!invitationToken) {
  invitationMessage.textContent = "Liên kết lời mời không hợp lệ hoặc thiếu mã.";
} else if (!localStorage.getItem("access_token") && !localStorage.getItem("token")) {
  const next = `${window.location.pathname}${window.location.search}`;
  window.location.assign(`login.html?next=${encodeURIComponent(next)}`);
} else {
  invitationMessage.textContent = "Đăng nhập bằng tài khoản có email được mời, sau đó chọn chấp nhận hoặc từ chối.";
  acceptButton.hidden = false;
  declineButton.hidden = false;
}

acceptButton.addEventListener("click", async () => {
  acceptButton.disabled = true;
  try {
    const result = await api.post(`/invitations/accept/${encodeURIComponent(invitationToken)}`);
    showToast(result.message);
    window.location.assign(`project.html?project=${result.project_id}`);
  } catch (error) {
    invitationMessage.textContent = error.message;
    showToast(error.message, "error");
    acceptButton.disabled = false;
  }
});

declineButton.addEventListener("click", async () => {
  declineButton.disabled = true;
  try {
    const result = await api.post(`/invitations/decline/${encodeURIComponent(invitationToken)}`);
    showToast(result.message);
    window.location.assign("invitations.html");
  } catch (error) {
    invitationMessage.textContent = error.message;
    showToast(error.message, "error");
    declineButton.disabled = false;
  }
});
