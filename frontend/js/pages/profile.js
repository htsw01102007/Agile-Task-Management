const profileForm = document.getElementById("profile-form");
const profileError = document.getElementById("profile-error");
let profileUser = null;

function renderProfile(user) {
  profileUser = user;
  document.getElementById("profile-name-heading").textContent = user.full_name || "Tài khoản";
  document.getElementById("profile-role").textContent = user.system_role === "admin" ? "Quản trị viên" : "Thành viên";
  document.getElementById("profile-avatar").textContent = layoutInitials(user.full_name || user.email || "?");
  profileForm.elements.full_name.value = user.full_name || "";
  profileForm.elements.email.value = user.email || "";
  profileForm.elements.username.value = user.username || "";
  profileForm.hidden = false;
  profileError.hidden = true;
}

async function loadProfile() {
  try {
    renderProfile(await api.get("/auth/me"));
  } catch (error) {
    profileError.textContent = error.message;
    profileError.hidden = false;
  }
}

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fullName = profileForm.elements.full_name.value.trim();
  if (!fullName) {
    showToast("Vui lòng nhập họ và tên.", "error");
    return;
  }
  const button = document.getElementById("profile-save");
  button.disabled = true;
  try {
    const updatedUser = await api.put("/auth/me", { full_name: fullName });
    renderProfile(updatedUser);
    window.dispatchEvent(new CustomEvent("layout:user-loaded", { detail: updatedUser }));
    showToast("Đã cập nhật họ tên.");
  } catch (error) {
    showToast(error.message, "error");
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
    const currentPassword = passwordForm.elements.current_password.value;
    const newPassword = passwordForm.elements.new_password.value;
    if (newPassword.length < 8 || !/[A-Z]/.test(newPassword) || !/[a-z]/.test(newPassword) || !/\d/.test(newPassword)) {
      showToast("Mật khẩu mới cần tối thiểu 8 ký tự, chữ hoa, chữ thường và số.", "error");
      return;
    }
    const button = document.getElementById("password-save");
    button.disabled = true;
    try {
      const res = await api.post("/auth/me/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      passwordForm.reset();
      showToast(res.message || "Đổi mật khẩu thành công.");
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  });
}

loadProfile();
