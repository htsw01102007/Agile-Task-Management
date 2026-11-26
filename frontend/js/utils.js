// ==========================================================================
// Hệ thống Biểu tượng Minimalist Monoline SVG & Hàm tiện ích dùng chung
// ==========================================================================

const MINIMAL_ICONS = {
  logo: '<svg class="icon icon-logo" viewBox="0 0 24 24" fill="none"><path d="M5.5 18.5L12 5.5L18.5 18.5" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/><path d="M8.5 14H15.5" stroke="currentColor" stroke-opacity="0.75" stroke-width="2.1" stroke-linecap="round"/></svg>',
  menu: '<svg class="icon" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2.5"/><line x1="9" y1="4" x2="9" y2="20"/></svg>',
  search: '<svg class="icon" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><line x1="20" y1="20" x2="16.2" y2="16.2"/></svg>',
  bell: '<svg class="icon" viewBox="0 0 24 24"><path d="M18 8.5a6 6 0 0 0-12 0c0 6.5-2.5 8.5-2.5 8.5h17S18 15 18 8.5"/><path d="M13.73 20.5a2 2 0 0 1-3.46 0"/></svg>',
  home: '<svg class="icon" viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="7" height="7" rx="1.75"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.75"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.75"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.75"/></svg>',
  grid: '<svg class="icon" viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/></svg>',
  list: '<svg class="icon" viewBox="0 0 24 24"><line x1="8" y1="6" x2="20" y2="6"/><line x1="8" y1="12" x2="20" y2="12"/><line x1="8" y1="18" x2="20" y2="18"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/></svg>',
  columns: '<svg class="icon" viewBox="0 0 24 24"><rect x="3" y="4" width="5" height="16" rx="1.5"/><rect x="9.5" y="4" width="5" height="11" rx="1.5"/><rect x="16" y="4" width="5" height="14" rx="1.5"/></svg>',
  table: '<svg class="icon" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="3" y1="9.5" x2="21" y2="9.5"/><line x1="3" y1="14.5" x2="21" y2="14.5"/><line x1="9" y1="9.5" x2="9" y2="20"/></svg>',
  tasks: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><path d="m8.75 12.25 2.25 2.25 4.5-4.75"/></svg>',
  check: '<svg class="icon" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
  circle: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/></svg>',
  mail: '<svg class="icon" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
  user: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.75"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/></svg>',
  users: '<svg class="icon" viewBox="0 0 24 24"><circle cx="9.5" cy="8" r="3.25"/><path d="M4 19.5a5.5 5.5 0 0 1 11 0"/><circle cx="17" cy="9" r="2.5"/><path d="M16.5 14.5a4.5 4.5 0 0 1 4 4.5"/></svg>',
  shield: '<svg class="icon" viewBox="0 0 24 24"><path d="M12 21s7-3.5 7-9.5V5.5L12 3 5 5.5v6C5 17.5 12 21 12 21z"/></svg>',
  lock: '<svg class="icon" viewBox="0 0 24 24"><rect x="4.5" y="11" width="15" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
  plus: '<svg class="icon" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  close: '<svg class="icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  edit: '<svg class="icon" viewBox="0 0 24 24"><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>',
  trash: '<svg class="icon" viewBox="0 0 24 24"><path d="M4 7h16"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/><path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"/></svg>',
  refresh: '<svg class="icon" viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><polyline points="21 3 21 9 15 9"/></svg>',
  more: '<svg class="icon" viewBox="0 0 24 24"><circle cx="6" cy="12" r="1.25"/><circle cx="12" cy="12" r="1.25"/><circle cx="18" cy="12" r="1.25"/></svg>',
  clock: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><polyline points="12 7.5 12 12 15.25 14"/></svg>',
  alert: '<svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5"/><line x1="12" y1="8" x2="12" y2="12.5"/><circle cx="12" cy="16" r="0.6" fill="currentColor"/></svg>',
  activity: '<svg class="icon" viewBox="0 0 24 24"><polyline points="21 12 17 12 14.5 19 9.5 5 7 12 3 12"/></svg>',
  layers: '<svg class="icon" viewBox="0 0 24 24"><polygon points="12 3 3 8 12 13 21 8 12 3"/><polyline points="3 13 12 18 21 13"/><polyline points="3 17.5 12 22.5 21 17.5"/></svg>',
  eye: '<svg class="icon" viewBox="0 0 24 24"><path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="2.75"/></svg>',
  eyeOff: '<svg class="icon" viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 18.5C5.5 18.5 2 12 2 12a16.6 16.6 0 0 1 4.06-4.94"/><path d="M9.9 5.68A9.12 9.12 0 0 1 12 5.5C18.5 5.5 22 12 22 12a16.8 16.8 0 0 1-2.16 3.19"/><line x1="3" y1="3" x2="21" y2="21"/></svg>',
  file: '<svg class="icon" viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><polyline points="14 3 14 8 19 8"/></svg>',
  paperclip: '<svg class="icon" viewBox="0 0 24 24"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>',
  logout: '<svg class="icon" viewBox="0 0 24 24"><path d="M9 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
  arrowRight: '<svg class="icon" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="13 6 19 12 13 18"/></svg>',
  arrowLeft: '<svg class="icon" viewBox="0 0 24 24"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="11 18 5 12 11 6"/></svg>',
  tag: '<svg class="icon" viewBox="0 0 24 24"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><circle cx="7" cy="7" r="1.25" fill="currentColor"/></svg>',
  chevronUp: '<svg class="icon" viewBox="0 0 24 24"><polyline points="17 14 12 9 7 14"/></svg>',
  grip: '<svg class="icon" viewBox="0 0 24 24"><circle cx="9" cy="6" r="1.35" fill="currentColor" stroke="none"/><circle cx="15" cy="6" r="1.35" fill="currentColor" stroke="none"/><circle cx="9" cy="12" r="1.35" fill="currentColor" stroke="none"/><circle cx="15" cy="12" r="1.35" fill="currentColor" stroke="none"/><circle cx="9" cy="18" r="1.35" fill="currentColor" stroke="none"/><circle cx="15" cy="18" r="1.35" fill="currentColor" stroke="none"/></svg>',
  sparkle: '<svg class="icon" viewBox="0 0 24 24"><path d="M12 3l2.2 6.8L21 12l-6.8 2.2L12 21l-2.2-6.8L3 12l6.8-2.2L12 3z"/></svg>',
};

function iconSvg(name) {
  return MINIMAL_ICONS[name] || "";
}

function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => {
    const key = el.dataset.icon;
    if (MINIMAL_ICONS[key]) {
      el.innerHTML = MINIMAL_ICONS[key];
    }
  });
  root.querySelectorAll(".mark").forEach((el) => {
    if (!el.querySelector("svg")) {
      el.innerHTML = MINIMAL_ICONS.logo;
    }
  });
}

// Chống XSS: luôn dùng hàm này khi chèn dữ liệu người dùng nhập vào innerHTML
function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

// 45000 -> "45.000 ₫"
function formatMoney(value) {
  return Number(value).toLocaleString("vi-VN") + " ₫";
}

// "2026-11-04T09:30:00" -> "09:30 4/11/2026"
function formatDateTime(value) {
  const d = new Date(value);
  return d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) + " " +
    d.toLocaleDateString("vi-VN");
}

// Hiện thông báo nhỏ ở góc màn hình. type: "success" | "error"
function showToast(message, type = "success") {
  let container = document.getElementById("toasts");
  if (!container) {
    container = document.createElement("div");
    container.id = "toasts";
    container.setAttribute("role", "status");
    container.setAttribute("aria-live", "polite");
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast toast-${type === "error" ? "error" : "success"}`;
  const icon = document.createElement("span");
  icon.className = "t-ic";
  icon.setAttribute("aria-hidden", "true");
  icon.innerHTML = type === "error" ? iconSvg("alert") : iconSvg("check");
  const text = document.createElement("span");
  text.className = "t-msg";
  text.textContent = message;
  const close = document.createElement("button");
  close.className = "t-x";
  close.type = "button";
  close.setAttribute("aria-label", "Đóng thông báo");
  close.innerHTML = iconSvg("close");
  close.addEventListener("click", () => toast.remove());
  toast.append(icon, text, close);
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4200);
}

// ==========================================================================
// Hệ thống kiểm tra dữ liệu đầu vào (Inline Field Validation)
// ==========================================================================

function _getErrorAnchor(input) {
  return input.closest(".input-with-btn") || input;
}

function setFieldError(input, message) {
  if (!input) return;
  input.classList.add("input-invalid");
  input.setAttribute("aria-invalid", "true");
  const anchor = _getErrorAnchor(input);
  let errEl = anchor.nextElementSibling;
  if (!errEl || !errEl.classList.contains("field-error")) {
    errEl = document.createElement("small");
    errEl.className = "field-error";
    errEl.setAttribute("role", "alert");
    anchor.insertAdjacentElement("afterend", errEl);
  }
  errEl.textContent = message;
}

function clearFieldError(input) {
  if (!input) return;
  input.classList.remove("input-invalid");
  input.removeAttribute("aria-invalid");
  const anchor = _getErrorAnchor(input);
  const errEl = anchor.nextElementSibling;
  if (errEl && errEl.classList.contains("field-error")) {
    errEl.remove();
  }
}

function clearFormErrors(form) {
  if (!form) return;
  form.querySelectorAll(".input-invalid").forEach((el) => {
    el.classList.remove("input-invalid");
    el.removeAttribute("aria-invalid");
  });
  form.querySelectorAll(".field-error").forEach((el) => el.remove());
}

function _requiredMessage(input) {
  const name = input.name || input.id || "";
  const map = {
    identifier: "Vui lòng nhập Email hoặc tên đăng nhập.",
    password: "Vui lòng nhập mật khẩu.",
    current_password: "Vui lòng nhập mật khẩu hiện tại.",
    new_password: "Vui lòng nhập mật khẩu mới.",
    full_name: "Vui lòng nhập họ và tên.",
    email: "Vui lòng nhập địa chỉ Email.",
    invitee_email: "Vui lòng nhập địa chỉ Email người nhận.",
    username: "Vui lòng nhập tên đăng nhập.",
    name: "Vui lòng nhập tên không được để trống.",
    title: "Vui lòng nhập tiêu đề công việc.",
    content: "Vui lòng nhập nội dung.",
  };
  return map[name] || "Vui lòng không để trống trường này.";
}

function validateField(input) {
  if (!input || input.disabled || input.hidden || input.type === "hidden" || input.readOnly) {
    return true;
  }

  const rawVal = input.value ?? "";
  const val = typeof rawVal === "string" ? rawVal.trim() : "";
  const name = input.name || input.id || "";
  const formId = input.form?.id || "";

  if (input.hasAttribute("required") && !val) {
    setFieldError(input, _requiredMessage(input));
    return false;
  }

  if (!val) {
    clearFieldError(input);
    return true;
  }

  if (input.type === "email") {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(val)) {
      setFieldError(input, "Địa chỉ Email không hợp lệ (VD: ten@congty.vn).");
      return false;
    }
  }

  if (name === "username") {
    if (val.length < 3) {
      setFieldError(input, "Tên đăng nhập phải có ít nhất 3 ký tự.");
      return false;
    }
    if (!/^[A-Za-z0-9_]+$/.test(val)) {
      setFieldError(input, "Tên đăng nhập chỉ gồm chữ cái không dấu, số và dấu gạch dưới (_).");
      return false;
    }
  }

  const isStrongPwField =
    input.id === "register-password" ||
    input.id === "new-password" ||
    (formId === "create-user-form" && name === "password");

  if (isStrongPwField) {
    if (rawVal.length < 8) {
      setFieldError(input, "Mật khẩu phải có tối thiểu 8 ký tự.");
      return false;
    }
    if (!/[A-Z]/.test(rawVal) || !/[a-z]/.test(rawVal) || !/\d/.test(rawVal)) {
      setFieldError(input, "Mật khẩu phải có đủ chữ hoa (A-Z), chữ thường (a-z) và chữ số (0-9).");
      return false;
    }
  }

  const minLen = Number(input.getAttribute("minlength") || 0);
  if (minLen > 0 && rawVal.length < minLen) {
    setFieldError(input, `Vui lòng nhập tối thiểu ${minLen} ký tự.`);
    return false;
  }

  if (input.type === "number" && input.hasAttribute("min")) {
    const minVal = Number(input.getAttribute("min"));
    if (Number(val) < minVal) {
      setFieldError(input, `Giá trị không được nhỏ hơn ${minVal}.`);
      return false;
    }
  }

  clearFieldError(input);
  return true;
}

function validateForm(form) {
  if (!form) return true;
  let isValid = true;
  let firstInvalid = null;

  const controls = form.querySelectorAll("input, textarea, select");
  controls.forEach((control) => {
    const ok = validateField(control);
    if (!ok) {
      isValid = false;
      if (!firstInvalid) firstInvalid = control;
    }
  });

  const startInput = form.elements?.start_date;
  const endInput = form.elements?.end_date || form.elements?.due_date;
  if (startInput?.value && endInput?.value) {
    if (new Date(endInput.value) < new Date(startInput.value)) {
      setFieldError(endInput, "Thời gian kết thúc không được sớm hơn thời gian bắt đầu.");
      isValid = false;
      if (!firstInvalid) firstInvalid = endInput;
    }
  }

  if (firstInvalid) {
    firstInvalid.focus();
  }
  return isValid;
}

function applyApiErrorsToForm(form, error) {
  if (!form || !error) return false;
  let matched = false;
  const msg = String(error.message || "");
  const lower = msg.toLowerCase();

  if (Array.isArray(error.data?.detail)) {
    error.data.detail.forEach((item) => {
      const fieldName = item.loc?.[item.loc.length - 1];
      const input = fieldName ? form.elements?.[fieldName] : null;
      if (input) {
        setFieldError(input, item.msg || msg);
        matched = true;
      }
    });
    if (matched) return true;
  }

  if (form.id === "login-form" && (error.status === 401 || lower.includes("mật khẩu") || lower.includes("đăng nhập"))) {
    if (form.elements.identifier) form.elements.identifier.classList.add("input-invalid");
    if (form.elements.password) setFieldError(form.elements.password, msg);
    return true;
  }

  if (lower.includes("email") && (form.elements?.email || form.elements?.invitee_email)) {
    setFieldError(form.elements.email || form.elements.invitee_email, msg);
    matched = true;
  }
  if ((lower.includes("tên đăng nhập") || lower.includes("username")) && form.elements?.username) {
    setFieldError(form.elements.username, msg);
    matched = true;
  }
  if (lower.includes("mật khẩu hiện tại") && form.elements?.current_password) {
    setFieldError(form.elements.current_password, msg);
    matched = true;
  } else if (lower.includes("mật khẩu") && (form.elements?.new_password || form.elements?.password)) {
    setFieldError(form.elements.new_password || form.elements.password, msg);
    matched = true;
  }
  if ((lower.includes("hạn chót") || lower.includes("ngày kết thúc")) && (form.elements?.due_date || form.elements?.end_date)) {
    setFieldError(form.elements.due_date || form.elements.end_date, msg);
    matched = true;
  }

  return matched;
}

function initInlineFormValidation() {
  hydrateIcons(document);
  document.querySelectorAll("form").forEach((form) => {
    form.setAttribute("novalidate", "novalidate");
  });

  document.addEventListener(
    "submit",
    (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;
      form.setAttribute("novalidate", "novalidate");
      if (!validateForm(form)) {
        event.preventDefault();
        event.stopImmediatePropagation();
      }
    },
    true,
  );

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement) {
      if (target.classList.contains("input-invalid")) {
        validateField(target);
      }
      if (target.form?.id === "login-form") {
        clearFieldError(target.form.elements.identifier);
        clearFieldError(target.form.elements.password);
      }
    }
  });

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement) {
      if (target.classList.contains("input-invalid")) {
        validateField(target);
      }
    }
  });

  document.addEventListener("reset", (event) => {
    if (event.target instanceof HTMLFormElement) {
      clearFormErrors(event.target);
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initInlineFormValidation);
} else {
  initInlineFormValidation();
}

// ==========================================================================
// Hệ thống Hộp thoại Nhập liệu & Xác nhận Tùy chỉnh (Thay thế window.prompt / confirm)
// ==========================================================================

function showPromptModal({
  eyebrow = "CẬP NHẬT DỮ LIỆU",
  title = "Nhập thông tin",
  description = "",
  label = "Giá trị *",
  defaultValue = "",
  placeholder = "",
  maxlength = 150,
  submitText = "Lưu thay đổi",
  requiredMessage = "Vui lòng không để trống trường này.",
} = {}) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "app-dialog app-dialog-compact";
    dialog.innerHTML = `
      <form class="dialog-form" novalidate>
        <div class="dialog-heading">
          <div>
            <p class="eyebrow">${escapeHtml(eyebrow)}</p>
            <h2>${escapeHtml(title)}</h2>
          </div>
          <button class="icon-btn" type="button" data-modal-cancel aria-label="Đóng">${iconSvg("close")}</button>
        </div>
        ${description ? `<p class="muted" style="margin: 0 0 12px; font-size: 12.5px;">${escapeHtml(description)}</p>` : ""}
        <label for="custom-prompt-input">${escapeHtml(label)}</label>
        <input
          id="custom-prompt-input"
          name="prompt_value"
          type="text"
          maxlength="${Number(maxlength) || 150}"
          placeholder="${escapeHtml(placeholder)}"
          value="${escapeHtml(defaultValue)}"
          required
        >
        <div class="dialog-actions">
          <button class="btn" type="button" data-modal-cancel>Huỷ</button>
          <button class="btn btn-primary" type="submit">${escapeHtml(submitText)}</button>
        </div>
      </form>
    `;

    document.body.appendChild(dialog);
    const form = dialog.querySelector("form");
    const input = dialog.querySelector("#custom-prompt-input");
    let settled = false;

    const cleanup = (result) => {
      if (settled) return;
      settled = true;
      if (dialog.open) dialog.close();
      dialog.remove();
      resolve(result);
    };

    dialog.querySelectorAll("[data-modal-cancel]").forEach((btn) => {
      btn.addEventListener("click", () => cleanup(null));
    });

    dialog.addEventListener("cancel", (e) => {
      e.preventDefault();
      cleanup(null);
    });

    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) cleanup(null);
    });

    input.addEventListener("input", () => {
      if (input.value.trim()) clearFieldError(input);
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const val = input.value.trim();
      if (!val) {
        setFieldError(input, requiredMessage);
        input.focus();
        return;
      }
      cleanup(val);
    });

    dialog.showModal();
    input.focus();
    input.select();
  });
}

function showConfirmModal({
  eyebrow = "XÁC NHẬN THAO TÁC",
  title = "Bạn có chắc chắn?",
  message = "Thao tác này sẽ cập nhật dữ liệu trên hệ thống.",
  confirmText = "Xác nhận",
  cancelText = "Huỷ",
  danger = false,
} = {}) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "app-dialog app-dialog-compact";
    dialog.innerHTML = `
      <div class="dialog-form">
        <div class="dialog-heading">
          <div>
            <p class="eyebrow">${escapeHtml(eyebrow)}</p>
            <h2>${escapeHtml(title)}</h2>
          </div>
          <button class="icon-btn" type="button" data-modal-cancel aria-label="Đóng">${iconSvg("close")}</button>
        </div>
        <p class="confirm-message">${escapeHtml(message)}</p>
        <div class="dialog-actions">
          <button class="btn" type="button" data-modal-cancel>${escapeHtml(cancelText)}</button>
          <button class="btn ${danger ? "btn-danger" : "btn-primary"}" type="button" data-modal-confirm>${escapeHtml(confirmText)}</button>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);
    let settled = false;

    const cleanup = (result) => {
      if (settled) return;
      settled = true;
      if (dialog.open) dialog.close();
      dialog.remove();
      resolve(result);
    };

    dialog.querySelectorAll("[data-modal-cancel]").forEach((btn) => {
      btn.addEventListener("click", () => cleanup(false));
    });
    dialog.querySelector("[data-modal-confirm]").addEventListener("click", () => cleanup(true));
    dialog.addEventListener("cancel", (e) => {
      e.preventDefault();
      cleanup(false);
    });
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) cleanup(false);
    });

    dialog.showModal();
    dialog.querySelector("[data-modal-confirm]").focus();
  });
}

function showLabelModal(existingLabel = null) {
  const presets = ["#5E6AD2", "#10B981", "#F59E0B", "#EF4444", "#0EA5E9", "#8B5CF6", "#EC4899", "#64748B"];
  const isEdit = Boolean(existingLabel && existingLabel.id);
  const initialName = existingLabel?.name || "";
  const initialColor = (existingLabel?.color || presets[0]).toUpperCase();
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "app-dialog app-dialog-compact";
    dialog.innerHTML = `
      <form class="dialog-form" novalidate>
        <div class="dialog-heading">
          <div>
            <p class="eyebrow">PHÂN LOẠI CÔNG VIỆC</p>
            <h2>${isEdit ? "Chỉnh sửa nhãn màu" : "Tạo nhãn màu mới"}</h2>
          </div>
          <button class="icon-btn" type="button" data-modal-cancel aria-label="Đóng">${iconSvg("close")}</button>
        </div>

        <label for="custom-label-name">Tên nhãn hiển thị *</label>
        <input id="custom-label-name" name="name" type="text" maxlength="50" value="${escapeHtml(initialName)}" placeholder="VD: Backend, UI/UX, Khẩn cấp…" required>

        <label style="margin-top: 14px;">Chọn màu sắc nhận diện</label>
        <div class="color-picker-row">
          <div class="color-swatches">
            ${presets.map((hex) => `<button type="button" class="color-swatch ${hex.toUpperCase() === initialColor ? "active" : ""}" data-color="${hex}" style="background:${hex};" aria-label="Màu ${hex}"></button>`).join("")}
          </div>
          <input id="custom-label-color" class="color-input-native" type="color" value="${escapeHtml(initialColor)}" title="Tùy chọn màu bất kỳ">
        </div>

        <div class="dialog-actions">
          <button class="btn" type="button" data-modal-cancel>Huỷ</button>
          <button class="btn btn-primary" type="submit">${iconSvg(isEdit ? "check" : "plus")}<span>${isEdit ? "Lưu nhãn" : "Tạo nhãn"}</span></button>
        </div>
      </form>
    `;

    document.body.appendChild(dialog);
    const form = dialog.querySelector("form");
    const nameInput = dialog.querySelector("#custom-label-name");
    const colorInput = dialog.querySelector("#custom-label-color");
    let settled = false;

    const cleanup = (result) => {
      if (settled) return;
      settled = true;
      if (dialog.open) dialog.close();
      dialog.remove();
      resolve(result);
    };

    dialog.querySelectorAll(".color-swatch").forEach((swatch) => {
      swatch.addEventListener("click", () => {
        dialog.querySelectorAll(".color-swatch").forEach((s) => s.classList.remove("active"));
        swatch.classList.add("active");
        colorInput.value = swatch.dataset.color;
      });
    });

    colorInput.addEventListener("input", () => {
      dialog.querySelectorAll(".color-swatch").forEach((s) => s.classList.remove("active"));
    });

    dialog.querySelectorAll("[data-modal-cancel]").forEach((btn) => {
      btn.addEventListener("click", () => cleanup(null));
    });
    dialog.addEventListener("cancel", (e) => {
      e.preventDefault();
      cleanup(null);
    });
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) cleanup(null);
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = nameInput.value.trim();
      if (!name) {
        setFieldError(nameInput, "Vui lòng nhập tên nhãn phân loại.");
        nameInput.focus();
        return;
      }
      cleanup({ name, color: colorInput.value || "#5E6AD2" });
    });

    dialog.showModal();
    nameInput.focus();
  });
}

function showDeleteListModal(list, otherLists, hasTasks) {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "app-dialog app-dialog-compact";
    dialog.innerHTML = `
      <form class="dialog-form" novalidate>
        <div class="dialog-heading">
          <div>
            <p class="eyebrow">QUẢN LÝ CỘT KANBAN</p>
            <h2>Xoá cột "${escapeHtml(list.name)}"</h2>
          </div>
          <button class="icon-btn" type="button" data-modal-cancel aria-label="Đóng">${iconSvg("close")}</button>
        </div>
        <p class="confirm-message">
          ${hasTasks
            ? `Cột "${escapeHtml(list.name)}" đang chứa công việc. Vui lòng chọn cột đích để chuyển toàn bộ công việc sang trước khi xoá:`
            : `Bạn có chắc chắn muốn xoá cột "${escapeHtml(list.name)}" khỏi bảng Kanban không?`}
        </p>
        ${hasTasks ? `
          <label for="target-list-select" style="margin-top: 12px;">Chuyển công việc sang cột *</label>
          <select id="target-list-select" name="target_list_id">
            ${otherLists.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}</option>`).join("")}
          </select>
        ` : ""}
        <div class="dialog-actions">
          <button class="btn" type="button" data-modal-cancel>Huỷ</button>
          <button class="btn btn-danger" type="submit">Xoá cột trạng thái</button>
        </div>
      </form>
    `;

    document.body.appendChild(dialog);
    const form = dialog.querySelector("form");
    let settled = false;

    const cleanup = (result) => {
      if (settled) return;
      settled = true;
      if (dialog.open) dialog.close();
      dialog.remove();
      resolve(result);
    };

    dialog.querySelectorAll("[data-modal-cancel]").forEach((btn) => {
      btn.addEventListener("click", () => cleanup({ confirmed: false, targetListId: null }));
    });
    dialog.addEventListener("cancel", (e) => {
      e.preventDefault();
      cleanup({ confirmed: false, targetListId: null });
    });
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) cleanup({ confirmed: false, targetListId: null });
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const selectEl = dialog.querySelector("#target-list-select");
      cleanup({
        confirmed: true,
        targetListId: selectEl ? Number(selectEl.value) : null,
      });
    });

    dialog.showModal();
  });
}
