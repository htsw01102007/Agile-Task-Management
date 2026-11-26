-- =============================================================================
-- AGILE WORKSPACE (AGILE TASK MANAGEMENT) — SCRIPT KHỞI TẠO CSDL & DỮ LIỆU MẪU
-- Tương thích 100% với SQLAlchemy 2.0 Models trong backend/app/models/
-- Mật khẩu mặc định cho TẤT CẢ tài khoản mẫu bên dưới: Password@123
-- =============================================================================

CREATE DATABASE IF NOT EXISTS agile_task_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE agile_task_management;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS checklist_items;
DROP TABLE IF EXISTS task_labels;
DROP TABLE IF EXISTS labels;
DROP TABLE IF EXISTS task_assignees;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS lists;
DROP TABLE IF EXISTS project_invitations;
DROP TABLE IF EXISTS project_members;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS revoked_tokens;
DROP TABLE IF EXISTS password_reset_tokens;
DROP TABLE IF EXISTS oauth_accounts;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------
-- 1. BẢNG NGƯỜI DÙNG & XÁC THỰC (4 BẢNG)
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    username        VARCHAR(50)  NOT NULL,
    password_hash   VARCHAR(255) NULL,
    full_name       VARCHAR(150) NOT NULL,
    avatar_url      VARCHAR(500) NULL,
    system_role     ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    token_version   INT NOT NULL DEFAULT 0,
    last_login_at   DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_username UNIQUE (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE oauth_accounts (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id           BIGINT NOT NULL,
    provider          VARCHAR(50)  NOT NULL,
    provider_user_id  VARCHAR(255) NOT NULL,
    access_token      TEXT NULL,
    refresh_token     TEXT NULL,
    token_expires_at  DATETIME NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_oauth_provider_user UNIQUE (provider, provider_user_id),
    CONSTRAINT fk_oauth_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_oauth_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE password_reset_tokens (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    token_hash      CHAR(64) NOT NULL,
    expires_at      DATETIME NOT NULL,
    used_at         DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_prt_token UNIQUE (token_hash),
    CONSTRAINT fk_prt_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_prt_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE revoked_tokens (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    jti             VARCHAR(64) NOT NULL,
    expires_at      DATETIME NOT NULL,
    revoked_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_revoked_tokens_jti UNIQUE (jti),
    INDEX idx_revoked_tokens_jti (jti)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. BẢNG DỰ ÁN, THÀNH VIÊN & LỜI MỜI (3 BẢNG)
-- -----------------------------------------------------------------------------
CREATE TABLE projects (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    description     TEXT NULL,
    owner_id        BIGINT NOT NULL,
    status          ENUM('active', 'completed', 'archived') NOT NULL DEFAULT 'active',
    start_date      DATE NULL,
    end_date        DATE NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    CONSTRAINT fk_projects_owner FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT chk_projects_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
    INDEX idx_projects_owner (owner_id),
    INDEX idx_projects_status (status, deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE project_members (
    project_id      BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    role            ENUM('owner', 'manager', 'member', 'viewer') NOT NULL DEFAULT 'member',
    joined_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id),
    CONSTRAINT fk_pm_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_pm_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_pm_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE project_invitations (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT NOT NULL,
    inviter_id      BIGINT NULL,
    invitee_email   VARCHAR(255) NOT NULL,
    invitee_id      BIGINT NULL,
    role            ENUM('manager', 'member', 'viewer') NOT NULL DEFAULT 'member',
    token           CHAR(64) NOT NULL,
    status          ENUM('pending', 'accepted', 'declined', 'expired', 'cancelled') NOT NULL DEFAULT 'pending',
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at    DATETIME NULL,
    pending_email   VARCHAR(255) GENERATED ALWAYS AS (
                        CASE WHEN status = 'pending' THEN LOWER(invitee_email) ELSE NULL END
                    ) VIRTUAL,
    CONSTRAINT uq_invitations_token UNIQUE (token),
    CONSTRAINT uq_invitations_pending UNIQUE (project_id, pending_email),
    CONSTRAINT fk_inv_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_inv_inviter FOREIGN KEY (inviter_id) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_inv_invitee FOREIGN KEY (invitee_id) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_inv_project_status (project_id, status),
    INDEX idx_inv_email (invitee_email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. BẢNG CỘT KANBAN, NHÃN & CÔNG VIỆC (5 BẢNG)
-- -----------------------------------------------------------------------------
CREATE TABLE lists (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT NOT NULL,
    name            VARCHAR(100) NOT NULL,
    position        INT NOT NULL DEFAULT 0,
    is_done_column  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_lists_id_project UNIQUE (id, project_id),
    CONSTRAINT fk_lists_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    INDEX idx_lists_project_position (project_id, position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE labels (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT NOT NULL,
    name            VARCHAR(50) NOT NULL,
    color           CHAR(7) NOT NULL DEFAULT '#808080',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_labels_project_name UNIQUE (project_id, name),
    CONSTRAINT fk_labels_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tasks (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT NOT NULL,
    list_id         BIGINT NOT NULL,
    title           VARCHAR(500) NOT NULL,
    description     TEXT NULL,
    priority        ENUM('low', 'medium', 'high', 'urgent') NOT NULL DEFAULT 'medium',
    position        INT NOT NULL DEFAULT 0,
    start_date      DATETIME NULL,
    due_date        DATETIME NULL,
    completed_at    DATETIME NULL,
    created_by      BIGINT NOT NULL,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at      DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_tasks_list FOREIGN KEY (list_id, project_id) REFERENCES lists (id, project_id) ON DELETE CASCADE,
    CONSTRAINT fk_tasks_creator FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE RESTRICT,
    CONSTRAINT chk_tasks_dates CHECK (due_date IS NULL OR start_date IS NULL OR due_date >= start_date),
    INDEX idx_tasks_list_position (list_id, position),
    INDEX idx_tasks_project_due (project_id, due_date),
    INDEX idx_tasks_assignee_due (created_by, due_date),
    INDEX idx_tasks_is_deleted (is_deleted),
    FULLTEXT INDEX ftx_tasks_title_desc (title, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE task_assignees (
    task_id         BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    assigned_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, user_id),
    CONSTRAINT fk_ta_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_ta_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_ta_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE task_labels (
    task_id         BIGINT NOT NULL,
    label_id        BIGINT NOT NULL,
    PRIMARY KEY (task_id, label_id),
    CONSTRAINT fk_tl_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_tl_label FOREIGN KEY (label_id) REFERENCES labels (id) ON DELETE CASCADE,
    INDEX idx_tl_label (label_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. BẢNG CHECKLIST, BÌNH LUẬN, ĐÍNH KÈM, THÔNG BÁO & NHẬT KÝ (5 BẢNG)
-- -----------------------------------------------------------------------------
CREATE TABLE checklist_items (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id         BIGINT NOT NULL,
    content         VARCHAR(500) NOT NULL,
    is_done         BOOLEAN NOT NULL DEFAULT FALSE,
    position        INT NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_ci_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    INDEX idx_ci_task_position (task_id, position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE comments (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id         BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    content         TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_comments_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_comments_task_created (task_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE attachments (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id         BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    file_size       BIGINT NOT NULL,
    mime_type       VARCHAR(100) NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_att_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_att_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_att_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE notifications (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    type            ENUM(
                        'task_created',
                        'task_assigned',
                        'task_updated',
                        'task_moved',
                        'task_completed',
                        'task_deleted',
                        'task_overdue',
                        'task_due_soon',
                        'comment_added',
                        'comment_updated',
                        'comment_deleted',
                        'invitation_sent',
                        'invitation_accepted',
                        'invitation_declined',
                        'member_added',
                        'member_removed',
                        'member_role_changed',
                        'project_updated',
                        'deadline_reminder'
                    ) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    message         TEXT NULL,
    entity_type     VARCHAR(50) NULL,
    entity_id       BIGINT NULL,
    project_id      BIGINT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_notif_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    INDEX idx_notifications_user_read_created (user_id, is_read, created_at),
    INDEX idx_notifications_entity (entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE activity_logs (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT NOT NULL,
    task_id         BIGINT NULL,
    user_id         BIGINT NOT NULL,
    entity_type     VARCHAR(50) NOT NULL,
    entity_id       BIGINT NULL,
    action          VARCHAR(50) NOT NULL,
    old_value       TEXT NULL,
    new_value       TEXT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_al_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_al_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE SET NULL,
    CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_activity_project_created (project_id, created_at),
    INDEX idx_activity_task_created (task_id, created_at),
    INDEX idx_activity_user_created (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- DỮ LIỆU MẪU CHUẨN THUYẾT TRÌNH & DEMO (Mật khẩu chung: Password@123)
-- =============================================================================

-- 1. Tài khoản người dùng (Quản trị viên, Giảng viên hướng dẫn & 5 thành viên nhóm)
INSERT INTO users (id, email, username, password_hash, full_name, avatar_url, system_role, is_active, token_version, last_login_at, created_at) VALUES
(1, 'admin@agileworkspace.vn',     'admin',           '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Quản Trị Hệ Thống',     NULL, 'admin', TRUE,  0, '2026-11-26 08:00:00', '2026-09-01 08:00:00'),
(2, 'binh.nd@agileworkspace.vn',   'nghiemdinhbinh',  '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Nghiêm Đình Bình',      NULL, 'user',  TRUE,  0, '2026-11-26 08:30:00', '2026-09-01 08:15:00'),
(3, 'quydung.n@agileworkspace.vn', 'nguyenquydung',   '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Nguyễn Quý Dũng',       NULL, 'user',  TRUE,  0, '2026-11-26 08:45:00', '2026-09-01 08:20:00'),
(4, 'minhson.l@agileworkspace.vn', 'leminhson',       '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Lê Minh Sơn',           NULL, 'user',  TRUE,  0, '2026-11-26 09:00:00', '2026-09-01 08:25:00'),
(5, 'ducminh.h@agileworkspace.vn', 'haducminh',       '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Hà Đức Minh',           NULL, 'user',  TRUE,  0, '2026-11-26 09:10:00', '2026-09-01 08:30:00'),
(6, 'tandung.n@agileworkspace.vn', 'nguyentandung',   '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Nguyễn Tấn Dũng',       NULL, 'user',  TRUE,  0, '2026-11-26 09:15:00', '2026-09-01 08:35:00'),
(7, 'minhduong.nh@agileworkspace.vn', 'minhduong',    '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Nguyễn Hữu Minh Dương', NULL, 'user',  TRUE,  0, '2026-11-25 16:00:00', '2026-09-01 08:10:00'),
(8, 'locked.demo@agileworkspace.vn',  'taikhoankhoa', '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Tài Khoản Tạm Khóa',    NULL, 'user',  FALSE, 1, '2026-10-15 10:00:00', '2026-09-10 09:00:00');

-- 2. Danh mục 4 dự án mẫu (đủ 3 trạng thái: active, completed, archived)
INSERT INTO projects (id, name, description, owner_id, status, start_date, end_date, created_at, deleted_at) VALUES
(1, 'Phát triển Nền tảng Agile Workspace',          'Xây dựng hệ thống quản lý dự án & điều phối công việc nhóm theo thời gian thực với FastAPI, MySQL 8.0, WebSocket và giao diện Clean SaaS.', 2, 'active',    '2026-09-15', '2026-12-20', '2026-09-15 08:00:00', NULL),
(2, 'Xây dựng Sàn Thương mại Điện tử Đa kênh',       'Phát triển hệ thống đặt hàng trực tuyến tích hợp giỏ hàng thông minh, cổng thanh toán VNPay, quản lý tồn kho và đối soát đơn hàng.',       3, 'active',    '2026-10-01', '2027-01-30', '2026-10-01 09:00:00', NULL),
(3, 'Chuẩn hóa Hệ thống Giao diện Clean SaaS v2',   'Thiết kế bộ quy chuẩn màu sắc Linear Indigo, hệ thống icon tối giản đồng nhất và hộp thoại tương tác cho toàn bộ 12 trang giao diện.',      4, 'completed', '2026-09-01', '2026-10-30', '2026-09-01 08:30:00', NULL),
(4, 'Nghiên cứu Khả thi Ứng dụng Quản lý Học tập',  'Dự án tiền khả thi giai đoạn trước đã được chuyển vào kho lưu trữ chỉ đọc để bảo toàn tài liệu tham khảo (dùng demo nút Khôi phục / Xoá).', 2, 'archived',  '2026-07-01', '2026-08-31', '2026-07-01 08:00:00', NULL);

-- 3. Phân quyền thành viên trong từng dự án (đủ 4 vai trò: owner, manager, member, viewer)
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES
-- Dự án 1: Đầy đủ nhóm 5 thành viên + GVHD ở vai trò Viewer quan sát tiến độ
(1, 2, 'owner',   '2026-09-15 08:00:00'),
(1, 3, 'manager', '2026-09-15 08:05:00'),
(1, 4, 'member',  '2026-09-15 08:10:00'),
(1, 5, 'member',  '2026-09-15 08:15:00'),
(1, 6, 'member',  '2026-09-15 08:20:00'),
(1, 7, 'viewer',  '2026-09-16 09:00:00'),
-- Dự án 2: Nguyễn Quý Dũng làm Owner, Nghiêm Đình Bình làm Manager, Minh Sơn & Đức Minh làm Member
(2, 3, 'owner',   '2026-10-01 09:00:00'),
(2, 2, 'manager', '2026-10-01 09:10:00'),
(2, 4, 'member',  '2026-10-01 09:15:00'),
(2, 5, 'member',  '2026-10-01 09:20:00'),
-- Dự án 3 (Completed)
(3, 4, 'owner',   '2026-09-01 08:30:00'),
(3, 2, 'manager', '2026-09-01 08:35:00'),
(3, 5, 'member',  '2026-09-01 08:40:00'),
(3, 6, 'member',  '2026-09-01 08:45:00'),
-- Dự án 4 (Archived)
(4, 2, 'owner',   '2026-07-01 08:00:00'),
(4, 3, 'member',  '2026-07-01 08:15:00');

-- 4. Lời mời tham gia dự án mẫu (gồm cả lời mời đang chờ pending để demo trang Lời mời)
-- Token của id=2 tương ứng bản băm SHA-256 của chuỗi 'demo-invite-tandung-project-2'
INSERT INTO project_invitations (id, project_id, inviter_id, invitee_email, invitee_id, role, token, status, expires_at, created_at, responded_at) VALUES
(1, 1, 2, 'tandung.n@agileworkspace.vn',  6,    'member', '8725d63aae4082bc2ed532d570b7a44b6ae7519804ce86098ccab13628d142e8', 'accepted', '2026-09-22 08:20:00', '2026-09-15 08:18:00', '2026-09-15 08:20:00'),
(2, 2, 3, 'tandung.n@agileworkspace.vn',  6,    'member', 'd7066c8ea96e6c4ec0108dff12322fbe0c98beda55a084a57f7feb26db9d9245', 'pending',  '2026-12-31 23:59:59', '2026-11-25 14:00:00', NULL),
(3, 2, 3, 'minhduong.nh@agileworkspace.vn', 7,  'viewer', '2807abc18ff35aa28b2385a2adc72bfd40b90c89efbe29b330ff843d97139069', 'pending',  '2026-12-31 23:59:59', '2026-11-25 15:00:00', NULL),
(4, 1, 3, 'ctv.ben.ngoai@example.com',    NULL, 'viewer', 'b2d04ddec3ca17678eea9bbe128cd9b60a863584aa6393a101e0ff1f1e1029de', 'expired',  '2026-10-20 09:00:00', '2026-10-13 09:00:00', NULL);

-- 5. Các cột trạng thái Kanban (position đánh số chuẩn từ 0)
INSERT INTO lists (id, project_id, name, position, is_done_column, created_at) VALUES
-- Dự án 1 (4 cột quy trình Agile chuẩn)
(1,  1, 'Cần làm',            0, FALSE, '2026-09-15 08:00:00'),
(2,  1, 'Đang triển khai',    1, FALSE, '2026-09-15 08:00:00'),
(3,  1, 'Đang kiểm thử (QA)', 2, FALSE, '2026-09-15 08:00:00'),
(4,  1, 'Hoàn thành',         3, TRUE,  '2026-09-15 08:00:00'),
-- Dự án 2 (3 cột mặc định)
(5,  2, 'Cần làm',            0, FALSE, '2026-10-01 09:00:00'),
(6,  2, 'Đang làm',           1, FALSE, '2026-10-01 09:00:00'),
(7,  2, 'Hoàn thành',         2, TRUE,  '2026-10-01 09:00:00'),
-- Dự án 3 (3 cột mặc định)
(8,  3, 'Cần làm',            0, FALSE, '2026-09-01 08:30:00'),
(9,  3, 'Đang làm',           1, FALSE, '2026-09-01 08:30:00'),
(10, 3, 'Hoàn thành',         2, TRUE,  '2026-09-01 08:30:00'),
-- Dự án 4 (Lưu trữ)
(11, 4, 'Cần làm',            0, FALSE, '2026-07-01 08:00:00'),
(12, 4, 'Đang làm',           1, FALSE, '2026-07-01 08:00:00'),
(13, 4, 'Hoàn thành',         2, TRUE,  '2026-07-01 08:00:00');

-- 6. Nhãn màu phân loại (Labels)
INSERT INTO labels (id, project_id, name, color, created_at) VALUES
(1, 1, 'Database & ERD', '#D97706', '2026-09-15 08:30:00'),
(2, 1, 'Backend API',    '#2563EB', '2026-09-15 08:30:00'),
(3, 1, 'Frontend SaaS',  '#059669', '2026-09-15 08:30:00'),
(4, 1, 'Realtime WS',    '#7C3AED', '2026-09-15 08:30:00'),
(5, 1, 'Bảo mật & RBAC', '#DC2626', '2026-09-15 08:30:00'),
(6, 1, 'Kiểm thử QA',    '#0EA5E9', '2026-09-15 08:30:00'),
(7, 2, 'Thanh toán',     '#F59E0B', '2026-10-01 09:30:00'),
(8, 2, 'Giỏ hàng',       '#4F46E5', '2026-10-01 09:30:00'),
(9, 3, 'UI/UX Minimal',  '#EC4899', '2026-09-01 09:00:00');

-- 7. Danh sách công việc (Tasks) — Bao phủ đủ hoàn thành, đang làm, quá hạn, chưa giao & trong thùng rác
INSERT INTO tasks (id, project_id, list_id, title, description, priority, position, start_date, due_date, completed_at, created_by, is_deleted, deleted_at, created_at) VALUES
-- DỰ ÁN 1: Agile Workspace (11 việc đang mở + 1 việc trong Thùng rác)
(1,  1, 4, 'Thiết kế sơ đồ ERD 16 bảng chuẩn hóa 3NF',                 'Phân tích nghiệp vụ, thiết lập khóa ngoại kép (list_id, project_id) và cột ảo chống mời trùng.',             'high',   0, '2026-09-16 08:00:00', '2026-09-28 17:00:00', '2026-09-27 15:30:00', 2, FALSE, NULL,                  '2026-09-16 08:00:00'),
(2,  1, 4, 'Xây dựng xác thực JWT kép & Đăng nhập Google OAuth 2.0',   'Tích hợp Bcrypt 12 vòng, cơ chế Refresh Token tự động và liên kết tài khoản Google OpenID Connect.',         'high',   1, '2026-09-28 08:00:00', '2026-10-12 17:00:00', '2026-10-11 16:00:00', 4, FALSE, NULL,                  '2026-09-28 08:30:00'),
(3,  1, 4, 'Phát triển bộ phân quyền dự án RBAC 4 cấp độ',             'Kiểm soát chặt quyền Owner, Manager, Member, Viewer ở cả tầng REST API lẫn kết nối WebSocket.',              'high',   2, '2026-10-10 08:00:00', '2026-10-22 17:00:00', '2026-10-21 14:20:00', 4, FALSE, NULL,                  '2026-10-10 08:30:00'),
(4,  1, 4, 'Tái thiết kế giao diện Clean SaaS & Thanh tìm kiếm (/)',   'Đồng bộ logo tối giản, hộp thoại custom và thanh tìm kiếm điều hướng bằng phím mũi tên lên/xuống.',          'medium', 3, '2026-10-22 08:00:00', '2026-11-08 17:00:00', '2026-11-07 18:00:00', 2, FALSE, NULL,                  '2026-10-22 09:00:00'),
(5,  1, 4, 'Đồng bộ Realtime lời mời dự án & Kéo thả bảng Kanban',     'Đẩy thông báo tức thì qua /ws/notifications và đồng bộ di chuyển thẻ 0ms qua /ws/projects/{id}.',            'urgent', 4, '2026-11-08 08:00:00', '2026-11-22 17:00:00', '2026-11-21 20:15:00', 5, FALSE, NULL,                  '2026-11-08 08:30:00'),
(6,  1, 3, 'Xây dựng Tab Thống kê tỷ lệ công việc từng thành viên',    'Tính toán tỷ lệ % khối lượng đảm nhận trong dự án và thanh tiến độ cá nhân cho từng thành viên.',            'high',   0, '2026-11-20 08:00:00', '2026-12-02 17:00:00', NULL,                  6, FALSE, NULL,                  '2026-11-20 09:00:00'),
(7,  1, 3, 'Viết bộ kiểm thử tự động Pytest & Đặc tả nghiệm thu (AC)', 'Kiểm thử luồng xác thực, chống mời trùng, kiểm tra Magic Bytes tệp tải lên và thu hồi quyền WebSocket.',     'medium', 1, '2026-11-21 08:00:00', '2026-12-05 17:00:00', NULL,                  6, FALSE, NULL,                  '2026-11-21 09:30:00'),
(8,  1, 2, 'Tối ưu truy vấn thống kê Dashboard & Nhật ký hoạt động',   'Giảm truy vấn lặp N+1 khi tải danh sách dự án và bổ sung phân trang cho bảng activity_logs.',                'high',   0, '2026-11-18 08:00:00', '2026-12-08 17:00:00', NULL,                  3, FALSE, NULL,                  '2026-11-18 10:00:00'),
(9,  1, 2, 'Hoàn thiện bộ Slide thuyết trình & Kịch bản Live Demo',    'Chuẩn bị sơ đồ ERD trực quan, phân công lời dẫn 10 phút cho 5 thành viên và kiểm tra đường truyền Vercel.',  'urgent', 1, '2026-11-24 08:00:00', '2026-11-30 17:00:00', NULL,                  2, FALSE, NULL,                  '2026-11-24 08:00:00'),
-- 1 công việc quá hạn mẫu để hiển thị rõ cảnh báo đỏ trên Dashboard & Thống kê
(10, 1, 1, 'Tích hợp dịch vụ gửi Email SMTP tự động cho khách ngoài',  'Cấu hình hàng đợi gửi thư mời tự động qua SendGrid thay cho thao tác sao chép liên kết thủ công.',           'medium', 0, '2026-11-05 08:00:00', '2026-11-20 17:00:00', NULL,                  3, FALSE, NULL,                  '2026-11-05 09:00:00'),
-- 1 công việc chưa phân công (Unassigned) để hiển thị rõ nhóm 'Chưa giao cho thành viên'
(11, 1, 1, 'Nghiên cứu nâng cấp lưu trữ tệp đính kèm lên AWS S3',      'Đánh giá giải pháp Presigned URL để mở rộng dung lượng tệp tải lên trên môi trường đám mây.',                 'low',    1, '2026-12-01 08:00:00', '2026-12-18 17:00:00', NULL,                  2, FALSE, NULL,                  '2026-11-22 10:00:00'),
-- 1 công việc đã xóa mềm nằm trong Thùng rác để demo nút Khôi phục
(12, 1, 1, 'Thử nghiệm giao diện tối tự động theo giờ hệ thống',       'Đầu việc thử nghiệm tạm đưa vào Thùng rác (có thể bấm nút Thùng rác trên bảng để khôi phục ngay).',          'low',    2, NULL,                  NULL,                  NULL,                  5, TRUE,  '2026-11-23 16:00:00', '2026-11-10 09:00:00'),

-- DỰ ÁN 2: Sàn Thương mại Điện tử Đa kênh (5 việc)
(13, 2, 7, 'Thiết kế Schema Sản phẩm, Biến thể & Kho hàng',            'Chuẩn hóa bảng danh mục đa cấp, thuộc tính SKU và lịch sử xuất nhập tồn kho.',                               'high',   0, '2026-10-02 08:00:00', '2026-10-18 17:00:00', '2026-10-17 15:00:00', 3, FALSE, NULL,                  '2026-10-02 09:00:00'),
(14, 2, 7, 'Xây dựng API Giỏ hàng & Áp dụng mã giảm giá',              'Tính tổng tiền đơn hàng, kiểm tra điều kiện voucher và khóa tồn kho tạm thời khi thanh toán.',               'high',   1, '2026-10-20 08:00:00', '2026-11-10 17:00:00', '2026-11-09 16:45:00', 3, FALSE, NULL,                  '2026-10-20 09:00:00'),
(15, 2, 6, 'Tích hợp cổng thanh toán VNPay & Xác thực chữ ký IPN',     'Sinh URL thanh toán bảo mật HMAC-SHA512 và tự động cập nhật trạng thái đơn khi nhận Webhook.',                'urgent', 0, '2026-11-12 08:00:00', '2026-12-10 17:00:00', NULL,                  2, FALSE, NULL,                  '2026-11-12 08:30:00'),
(16, 2, 6, 'Xây dựng trang Quản trị Đơn hàng & Xuất hóa đơn PDF',      'Cho phép lọc đơn theo trạng thái vận chuyển và in phiếu giao hàng hàng loạt.',                               'medium', 1, '2026-11-18 08:00:00', '2026-12-15 17:00:00', NULL,                  4, FALSE, NULL,                  '2026-11-18 09:00:00'),
(17, 2, 5, 'Tối ưu bộ nhớ đệm danh sách sản phẩm bán chạy',            'Giảm thời gian phản hồi trang chủ dưới 100ms khi lượng truy cập tăng cao.',                                  'medium', 0, '2026-12-01 08:00:00', '2026-12-25 17:00:00', NULL,                  5, FALSE, NULL,                  '2026-11-22 14:00:00'),

-- DỰ ÁN 3: Completed (3 việc hoàn thành 100%)
(18, 3, 10, 'Thiết kế Logo hình học tối giản & Bộ màu Linear Indigo',  'Xây dựng bảng màu 60-30-10 đồng nhất giữa trang xác thực, Dashboard và bảng Kanban.',                        'high',   0, '2026-09-02 08:00:00', '2026-09-15 17:00:00', '2026-09-14 17:00:00', 4, FALSE, NULL,                  '2026-09-02 08:30:00'),
(19, 3, 10, 'Xây dựng thư viện Icon Vector nét mảnh đồng bộ',          'Thay thế toàn bộ biểu tượng rời rạc bằng hệ thống MINIMAL_ICONS sắc nét.',                                   'medium', 1, '2026-09-16 08:00:00', '2026-10-05 17:00:00', '2026-10-04 16:00:00', 5, FALSE, NULL,                  '2026-09-16 09:00:00'),
(20, 3, 10, 'Chuẩn hóa kiểm lỗi biểu mẫu trực tiếp (Inline Validation)','Hiển thị thông báo lỗi tiếng Việt rõ ràng ngay dưới từng ô nhập liệu.',                                     'high',   2, '2026-10-06 08:00:00', '2026-10-28 17:00:00', '2026-10-27 15:30:00', 6, FALSE, NULL,                  '2026-10-06 09:00:00'),

-- DỰ ÁN 4: Archived (2 việc lịch sử)
(21, 4, 13, 'Khảo sát nhu cầu quản lý lịch ôn tập của sinh viên',      'Tổng hợp 120 phiếu khảo sát nhu cầu nhắc lịch học và chia sẻ tài liệu nhóm.',                                'medium', 0, '2026-07-02 08:00:00', '2026-07-20 17:00:00', '2026-07-19 16:00:00', 2, FALSE, NULL,                  '2026-07-02 09:00:00'),
(22, 4, 12, 'Đánh giá phương án đồng bộ thời khóa biểu học kỳ',        'Tài liệu phân tích được lưu trữ tham khảo trước khi nhóm chuyển sang đề tài Agile Workspace.',               'low',    0, '2026-07-22 08:00:00', '2026-08-25 17:00:00', NULL,                  3, FALSE, NULL,                  '2026-07-22 09:00:00');

-- 8. Phân công người thực hiện (task_assignees) — Phân bổ đều cho cả 5 thành viên để biểu đồ Thống kê cực đẹp!
-- (Task #11 cố tình để trống người nhận để minh họa mục "Chưa giao cho thành viên")
INSERT INTO task_assignees (task_id, user_id, assigned_at) VALUES
-- Dự án 1
(1,  2, '2026-09-16 08:05:00'),
(1,  3, '2026-09-16 08:05:00'),
(2,  4, '2026-09-28 08:35:00'),
(3,  4, '2026-10-10 08:35:00'),
(3,  3, '2026-10-10 08:35:00'),
(4,  2, '2026-10-22 09:05:00'),
(4,  5, '2026-10-22 09:05:00'),
(5,  5, '2026-11-08 08:35:00'),
(5,  2, '2026-11-08 08:35:00'),
(6,  6, '2026-11-20 09:05:00'),
(6,  5, '2026-11-20 09:05:00'),
(7,  6, '2026-11-21 09:35:00'),
(8,  3, '2026-11-18 10:05:00'),
(9,  2, '2026-11-24 08:05:00'),
(9,  4, '2026-11-24 08:05:00'),
(9,  6, '2026-11-24 08:05:00'),
(10, 3, '2026-11-05 09:05:00'),
(12, 5, '2026-11-10 09:05:00'),
-- Dự án 2
(13, 3, '2026-10-02 09:05:00'),
(14, 3, '2026-10-20 09:05:00'),
(14, 4, '2026-10-20 09:05:00'),
(15, 2, '2026-11-12 08:35:00'),
(15, 4, '2026-11-12 08:35:00'),
(16, 5, '2026-11-18 09:05:00'),
(17, 5, '2026-11-22 14:05:00'),
-- Dự án 3
(18, 4, '2026-09-02 08:35:00'),
(19, 5, '2026-09-16 09:05:00'),
(20, 6, '2026-10-06 09:05:00'),
-- Dự án 4
(21, 2, '2026-07-02 09:05:00'),
(22, 3, '2026-07-22 09:05:00');

-- 9. Gắn nhãn cho công việc (task_labels)
INSERT INTO task_labels (task_id, label_id) VALUES
(1, 1),
(2, 2), (2, 5),
(3, 2), (3, 5),
(4, 3),
(5, 3), (5, 4),
(6, 3),
(7, 6),
(8, 1), (8, 2),
(9, 3), (9, 6),
(10, 2),
(11, 2),
(13, 8), (14, 8), (15, 7), (16, 8),
(18, 9), (19, 9), (20, 9);

-- 10. Danh sách kiểm tra con (checklist_items)
INSERT INTO checklist_items (task_id, content, is_done, position, created_at) VALUES
(5, 'Thiết lập WebSocket Connection Manager quản lý theo user_id và project_id', TRUE,  0, '2026-11-08 09:00:00'),
(5, 'Đẩy sự kiện notification_created ngay khi tạo hoặc phản hồi lời mời',       TRUE,  1, '2026-11-09 09:00:00'),
(5, 'Đồng bộ thao tác kéo thả thẻ Kanban giữa nhiều cửa sổ trình duyệt',         TRUE,  2, '2026-11-12 09:00:00'),
(5, 'Bổ sung cơ chế Heartbeat ping/pong 20 giây và tự kết nối lại sau 3 giây',   TRUE,  3, '2026-11-15 09:00:00'),
(6, 'Tổng hợp thanh tiến độ Hoàn thành / Đang triển khai / Quá hạn toàn dự án',  TRUE,  0, '2026-11-20 09:30:00'),
(6, 'Tính tỷ lệ % khối lượng đảm nhận của từng thành viên trên tổng số việc',    TRUE,  1, '2026-11-21 10:00:00'),
(6, 'Tách nhóm công việc chưa phân công để trưởng nhóm dễ rà soát',              TRUE,  2, '2026-11-22 14:00:00'),
(6, 'Kiểm thử hiển thị tự động cập nhật khi kéo thả thẻ sang cột Hoàn thành',   FALSE, 3, '2026-11-23 08:30:00'),
(9, 'Hoàn thiện sơ đồ ERD 16 bảng đưa vào Slide thuyết trình Canva',             TRUE,  0, '2026-11-25 08:00:00'),
(9, 'Phân công thời lượng thuyết trình 10 phút cho 5 thành viên nhóm',           TRUE,  1, '2026-11-25 09:00:00'),
(9, 'Chạy thử kịch bản Live Demo 2 màn hình song song trước buổi bảo vệ',        FALSE, 2, '2026-11-26 08:00:00'),
(15, 'Đăng ký tài khoản VNPay Sandbox và cấu hình biến môi trường',              TRUE,  0, '2026-11-12 09:00:00'),
(15, 'Xử lý đối soát chữ ký bảo mật HMAC-SHA512 tại endpoint IPN',               TRUE,  1, '2026-11-15 10:00:00'),
(15, 'Kiểm thử kịch bản thanh toán thất bại và hủy giao dịch',                   FALSE, 2, '2026-11-18 14:00:00');

-- 11. Bình luận trao đổi trong công việc (comments)
INSERT INTO comments (id, task_id, user_id, content, created_at) VALUES
(1, 5, 5, 'Mình đã nối xong WebSocket ở cả layout.js và project.js, giờ gửi lời mời hoặc kéo thả task là bên kia nhảy ngay lập tức không cần F5.', '2026-11-21 19:30:00'),
(2, 5, 2, 'Quá mượt! Mình vừa mở thử 2 trình duyệt song song để test, thẻ nhảy không bị nháy khung hình chút nào.',                                 '2026-11-21 20:05:00'),
(3, 6, 6, 'Tab Thống kê công việc đã bổ sung đầy đủ phần trăm khối lượng dự án của từng thành viên, nhờ Bình và Quý Dũng xem qua giao diện nhé.',   '2026-11-23 09:30:00'),
(4, 6, 3, 'Số liệu khớp chuẩn với API /board rồi, kể cả các task chưa giao cũng được gom riêng rất dễ theo dõi.',                                   '2026-11-23 10:15:00'),
(5, 8, 3, 'Đã bổ sung eager loading và gom nhóm COUNT theo project_id để tối ưu tốc độ tải trang Tổng quan.',                                       '2026-11-24 14:20:00'),
(6, 9, 4, 'Phần bảo mật RBAC và tìm kiếm phím tắt (/) mình đã chuẩn bị sẵn ví dụ để phối hợp demo cùng cả nhóm.',                                   '2026-11-25 20:00:00');

-- 12. Tệp đính kèm mẫu (attachments)
INSERT INTO attachments (id, task_id, user_id, file_name, file_path, file_size, mime_type, created_at) VALUES
(1, 1, 2, 'so_do_erd_agile_workspace_16_bang.png', 'erd_sample_preview.png',     312400,  'image/png',       '2026-09-27 15:00:00'),
(2, 7, 6, 'dac_ta_test_cases_va_ac_chi_tiet.pdf',  'test_cases_ac_summary.pdf',  845120,  'application/pdf', '2026-11-22 22:50:00'),
(3, 9, 2, 'kich_ban_thuyet_trinh_nhom_10_phut.pdf','presentation_script_v2.pdf', 524288,  'application/pdf', '2026-11-25 08:30:00');

-- 13. Trung tâm thông báo (notifications) — Khớp chuẩn cột & ENUM của Notification model
INSERT INTO notifications (id, user_id, type, title, message, entity_type, entity_id, project_id, is_read, created_at) VALUES
(1, 2, 'comment_added',       'Hà Đức Minh đã bình luận trong công việc #5',             'Hà Đức Minh: Mình đã nối xong WebSocket ở cả layout.js và project.js...',                                    'task',       5, 1, FALSE, '2026-11-21 19:30:00'),
(2, 2, 'comment_added',       'Nguyễn Tấn Dũng đã bình luận trong công việc #6',         'Nguyễn Tấn Dũng: Tab Thống kê công việc đã bổ sung đầy đủ phần trăm khối lượng dự án của từng thành viên.', 'task',       6, 1, FALSE, '2026-11-23 09:30:00'),
(3, 2, 'task_assigned',       'Bạn được phân công: Hoàn thiện bộ Slide thuyết trình',    'Công việc ưu tiên Khẩn cấp trước buổi bảo vệ đồ án học phần.',                                               'task',       9, 1, TRUE,  '2026-11-24 08:05:00'),
(4, 3, 'task_overdue',        'Cảnh báo quá hạn: Tích hợp dịch vụ gửi Email SMTP',       'Công việc #10 trong dự án «Phát triển Nền tảng Agile Workspace» đã quá hạn chót.',                           'task',      10, 1, FALSE, '2026-11-21 08:00:00'),
(5, 6, 'invitation_sent',     'Lời mời tham gia dự án: Xây dựng Sàn Thương mại Điện tử', 'Nguyễn Quý Dũng mời bạn tham gia dự án với vai trò Member.',                                                 'invitation', 2, 2, FALSE, '2026-11-25 14:00:00'),
(6, 7, 'invitation_sent',     'Lời mời quan sát dự án: Xây dựng Sàn Thương mại Điện tử', 'Nguyễn Quý Dũng mời thầy tham gia quan sát dự án với vai trò Viewer.',                                       'invitation', 3, 2, FALSE, '2026-11-25 15:00:00'),
(7, 4, 'task_assigned',       'Bạn được phân công: Hoàn thiện bộ Slide thuyết trình',    'Nghiêm Đình Bình đã thêm bạn cùng phối hợp chuẩn bị nội dung bảo vệ.',                                       'task',       9, 1, FALSE, '2026-11-24 08:05:00'),
(8, 5, 'task_completed',      'Hoàn thành: Đồng bộ Realtime lời mời & Kéo thả Kanban',   'Công việc #5 đã được chuyển sang cột Hoàn thành.',                                                           'task',       5, 1, TRUE,  '2026-11-21 20:15:00');

-- 14. Nhật ký hoạt động dự án (activity_logs)
INSERT INTO activity_logs (id, project_id, task_id, user_id, entity_type, entity_id, action, old_value, new_value, created_at) VALUES
(1,  1, NULL, 2, 'project',    1,  'created',     NULL,                        '{"name": "Phát triển Nền tảng Agile Workspace"}',                                      '2026-09-15 08:00:00'),
(2,  1, NULL, 2, 'member',     3,  'joined',      NULL,                        '{"user_id": 3, "role": "manager"}',                                                    '2026-09-15 08:05:00'),
(3,  1, 1,    2, 'task',       1,  'created',     NULL,                        '{"title": "Thiết kế sơ đồ ERD 16 bảng chuẩn hóa 3NF", "priority": "high"}',            '2026-09-16 08:00:00'),
(4,  1, 2,    4, 'task',       2,  'moved',       '{"list_id": 2}',            '{"list_id": 4}',                                                                       '2026-10-11 16:00:00'),
(5,  1, 5,    5, 'task',       5,  'moved',       '{"list_id": 3}',            '{"list_id": 4}',                                                                       '2026-11-21 20:15:00'),
(6,  1, 6,    6, 'task',       6,  'created',     NULL,                        '{"title": "Xây dựng Tab Thống kê tỷ lệ công việc từng thành viên", "priority": "high"}','2026-11-20 09:00:00'),
(7,  1, 12,   5, 'task',       12, 'deleted',     '{"is_deleted": false}',     '{"is_deleted": true}',                                                                 '2026-11-23 16:00:00'),
(8,  1, 9,    2, 'task',       9,  'created',     NULL,                        '{"title": "Hoàn thiện bộ Slide thuyết trình & Kịch bản Live Demo", "priority": "urgent"}','2026-11-24 08:00:00'),
(9,  2, NULL, 3, 'project',    2,  'created',     NULL,                        '{"name": "Xây dựng Sàn Thương mại Điện tử Đa kênh"}',                                  '2026-10-01 09:00:00'),
(10, 2, NULL, 3, 'invitation', 2,  'created',     NULL,                        '{"invitee_email": "tandung.n@agileworkspace.vn", "role": "member"}',                   '2026-11-25 14:00:00'),
(11, 4, NULL, 2, 'project',    4,  'updated',     '{"status": "active"}',      '{"status": "archived"}',                                                               '2026-09-01 09:00:00');
