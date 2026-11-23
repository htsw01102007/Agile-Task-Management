const profileForm = document.getElementById("profile-form");
const profileError = document.getElementById("profile-error");
const newPwInput = document.getElementById("new-password");
const pwBars = document.querySelectorAll("#profile-pw-meter .pw-bar");
const pwHint = document.getElementById("profile-pw-hint");
let profileUser = null;

function renderProfile(user) {
  profileUser = user;
  document.getElementById("profile-name-heading").textContent = user.full_name || "Tài khoản";
  document.getElementById("profile-role").textContent = user.system_role === "admin" ? "Quản trị viên hệ thống" : "Thành viên chính thức";
  document.getElementById("profile-avatar").textContent = layoutInitials(user.full_name || user.email || "?");
  const cardUsername = document.getElementById("profile-card-username");
  if (cardUsername) cardUsername.textContent = `@${user.username || "user"}`;
  profileForm.elements.full_name.value = user.full_name || "";
  profileForm.elements.email.value = user.email || "";
  profileForm.elements.username.value = user.username || "";
  profileForm.hidden = false;
  profileError.hidden = true;
}

async function loadProfile() {
  try {
    const [user, metrics] = await Promise.all([
      api.get("/auth/me"),
      api.get("/projects/dashboard/summary").catch(() => null),
    ]);
    renderProfile(user);
    if (metrics) {
      const projEl = document.getElementById("profile-card-projects");
      const compEl = document.getElementById("profile-card-completed");
      if (projEl) projEl.textContent = `${metrics.active_project_count} dự án`;
      if (compEl) compEl.textContent = `${metrics.completed_task_count} công việc`;
    }
  } catch (error) {
    profileError.textContent = error.message;
    profileError.hidden = false;
  }
}

newPwInput?.addEventListener("input", () => {
  const val = newPwInput.value;
  let score = 0;
  if (val.length >= 8) score += 1;
  if (/[A-Z]/.test(val)) score += 1;
  if (/[a-z]/.test(val)) score += 1;
  if (/\d/.test(val)) score += 1;
  const tone = score <= 1 ? "active-weak" : score <= 3 ? "active-medium" : "active-strong";
  pwBars.forEach((bar, idx) => {
    bar.className = "pw-bar";
    if (val.length > 0 && idx < score) bar.classList.add(tone);
  });
  if (pwHint) {
    pwHint.textContent = score === 4
      ? "✓ Mật khẩu mới đạt độ mạnh tiêu chuẩn."
      : "Mật khẩu mới cần tối thiểu 8 ký tự, gồm chữ hoa, chữ thường và chữ số.";
  }
});

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!validateForm(profileForm)) return;
  const fullName = profileForm.elements.full_name.value.trim();
  const button = document.getElementById("profile-save");
  button.disabled = true;
  try {
    const updatedUser = await api.put("/auth/me", { full_name: fullName });
    renderProfile(updatedUser);
    window.dispatchEvent(new CustomEvent("layout:user-loaded", { detail: updatedUser }));
    showToast("Đã cập nhật họ tên hiển thị.");
  } catch (error) {
    if (!applyApiErrorsToForm(profileForm, error)) {
      showToast(error.message, "error");
    }
  } finally {
    button.disabled = false;
  }
});

window.addEventListener("layout:user-loaded", (event) => {
  if (event.detail) renderProfile(event.detail);
});

const passwordForm = document.getElementById("password-form");
if (passwordForm) {
  passwordForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validateForm(passwordForm)) return;
    const currentPassword = passwordForm.elements.current_password.value;
    const newPassword = passwordForm.elements.new_password.value;
    const button = document.getElementById("password-save");
    button.disabled = true;
    try {
      const res = await api.post("/auth/me/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      passwordForm.reset();
      pwBars.forEach((bar) => { bar.className = "pw-bar"; });
      showToast(res.message || "Đổi mật khẩu thành công.");
    } catch (error) {
      if (!applyApiErrorsToForm(passwordForm, error)) {
        showToast(error.message, "error");
      }
    } finally {
      button.disabled = false;
    }
  });
}

loadProfile();
