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

loadProfile();
