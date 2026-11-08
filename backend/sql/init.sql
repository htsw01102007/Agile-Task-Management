CREATE DATABASE IF NOT EXISTS task_project_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE task_project_management;

CREATE TABLE users (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    username        VARCHAR(50)  NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(150) NOT NULL,
    avatar_url      VARCHAR(500) NULL,
    system_role     ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_username UNIQUE (username)
) ENGINE=InnoDB;

CREATE TABLE projects (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    description     TEXT NULL,
    owner_id        BIGINT UNSIGNED NOT NULL,
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
) ENGINE=InnoDB;

CREATE TABLE project_members (
    project_id      BIGINT UNSIGNED NOT NULL,
    user_id         BIGINT UNSIGNED NOT NULL,
    role            ENUM('owner', 'manager', 'member', 'viewer') NOT NULL DEFAULT 'member',
    joined_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id),
    CONSTRAINT fk_pm_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_pm_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_pm_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE project_invitations (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    inviter_id      BIGINT UNSIGNED NULL,
    invitee_email   VARCHAR(255) NOT NULL,
    invitee_id      BIGINT UNSIGNED NULL,
    role            ENUM('manager', 'member', 'viewer') NOT NULL DEFAULT 'member',
    token           CHAR(64) NOT NULL,
    status          ENUM('pending', 'accepted', 'declined', 'expired', 'cancelled') NOT NULL DEFAULT 'pending',
    expires_at      DATETIME NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at    DATETIME NULL,
    CONSTRAINT uq_invitations_token UNIQUE (token),
    CONSTRAINT fk_inv_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_inv_inviter FOREIGN KEY (inviter_id) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_inv_invitee FOREIGN KEY (invitee_id) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_inv_project_status (project_id, status),
    INDEX idx_inv_email (invitee_email)
) ENGINE=InnoDB;

CREATE TABLE lists (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(100) NOT NULL,
    position        INT UNSIGNED NOT NULL DEFAULT 0,
    is_done_column  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_lists_id_project UNIQUE (id, project_id),
    CONSTRAINT fk_lists_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    INDEX idx_lists_project_position (project_id, position)
) ENGINE=InnoDB;

CREATE TABLE tasks (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    list_id         BIGINT UNSIGNED NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT NULL,
    position        INT UNSIGNED NOT NULL DEFAULT 0,
    priority        ENUM('low', 'medium', 'high', 'urgent') NOT NULL DEFAULT 'medium',
    start_date      DATETIME NULL,
    due_date        DATETIME NULL,
    completed_at    DATETIME NULL,
    created_by      BIGINT UNSIGNED NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_tasks_list FOREIGN KEY (list_id, project_id) REFERENCES lists (id, project_id) ON DELETE CASCADE,
    CONSTRAINT fk_tasks_creator FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT chk_tasks_dates CHECK (due_date IS NULL OR start_date IS NULL OR due_date >= start_date),
    INDEX idx_tasks_list_position (list_id, position),
    INDEX idx_tasks_project_due (project_id, due_date),
    INDEX idx_tasks_project_priority (project_id, priority),
    INDEX idx_tasks_deleted (deleted_at),
    FULLTEXT INDEX ftx_tasks_title_desc (title, description)
) ENGINE=InnoDB;

CREATE TABLE task_assignees (
    task_id         BIGINT UNSIGNED NOT NULL,
    user_id         BIGINT UNSIGNED NOT NULL,
    assigned_by     BIGINT UNSIGNED NULL,
    assigned_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, user_id),
    CONSTRAINT fk_ta_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_ta_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_ta_assigner FOREIGN KEY (assigned_by) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_ta_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE comments (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_id         BIGINT UNSIGNED NOT NULL,
    user_id         BIGINT UNSIGNED NULL,
    parent_id       BIGINT UNSIGNED NULL,
    content         TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME NULL,
    CONSTRAINT fk_comments_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_comments_parent FOREIGN KEY (parent_id) REFERENCES comments (id) ON DELETE CASCADE,
    INDEX idx_comments_task_created (task_id, created_at),
    INDEX idx_comments_parent (parent_id)
) ENGINE=InnoDB;

CREATE TABLE activity_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    task_id         BIGINT UNSIGNED NULL,
    user_id         BIGINT UNSIGNED NULL,
    entity_type     ENUM('project', 'member', 'invitation', 'list', 'task', 'comment', 'label', 'checklist_item', 'attachment') NOT NULL,
    entity_id       BIGINT UNSIGNED NOT NULL,
    action          VARCHAR(50) NOT NULL,
    old_value       JSON NULL,
    new_value       JSON NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_al_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_al_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE SET NULL,
    CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_al_project_created (project_id, created_at),
    INDEX idx_al_task_created (task_id, created_at),
    INDEX idx_al_entity (entity_type, entity_id)
) ENGINE=InnoDB;

CREATE TABLE labels (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id      BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(50) NOT NULL,
    color           CHAR(7) NOT NULL DEFAULT '#808080',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_labels_project_name UNIQUE (project_id, name),
    CONSTRAINT fk_labels_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE task_labels (
    task_id         BIGINT UNSIGNED NOT NULL,
    label_id        BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (task_id, label_id),
    CONSTRAINT fk_tl_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_tl_label FOREIGN KEY (label_id) REFERENCES labels (id) ON DELETE CASCADE,
    INDEX idx_tl_label (label_id)
) ENGINE=InnoDB;

CREATE TABLE checklist_items (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_id         BIGINT UNSIGNED NOT NULL,
    content         VARCHAR(500) NOT NULL,
    is_done         BOOLEAN NOT NULL DEFAULT FALSE,
    position        INT UNSIGNED NOT NULL DEFAULT 0,
    completed_at    DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ci_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    INDEX idx_ci_task_position (task_id, position)
) ENGINE=InnoDB;

CREATE TABLE attachments (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_id         BIGINT UNSIGNED NOT NULL,
    comment_id      BIGINT UNSIGNED NULL,
    uploaded_by     BIGINT UNSIGNED NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    file_size       BIGINT UNSIGNED NOT NULL,
    mime_type       VARCHAR(100) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_att_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    CONSTRAINT fk_att_comment FOREIGN KEY (comment_id) REFERENCES comments (id) ON DELETE SET NULL,
    CONSTRAINT fk_att_user FOREIGN KEY (uploaded_by) REFERENCES users (id) ON DELETE SET NULL,
    INDEX idx_att_task (task_id)
) ENGINE=InnoDB;

CREATE TABLE notifications (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    actor_id        BIGINT UNSIGNED NULL,
    project_id      BIGINT UNSIGNED NULL,
    task_id         BIGINT UNSIGNED NULL,
    type            ENUM('task_assigned', 'task_due_soon', 'task_overdue', 'comment_added', 'mentioned', 'project_invited', 'member_joined', 'task_completed') NOT NULL,
    message         VARCHAR(500) NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_notif_actor FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_notif_project FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
    CONSTRAINT fk_notif_task FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
    INDEX idx_notif_user_read (user_id, is_read, created_at)
) ENGINE=InnoDB;

CREATE TABLE password_reset_tokens (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT UNSIGNED NOT NULL,
    token_hash      CHAR(64) NOT NULL,
    expires_at      DATETIME NOT NULL,
    used_at         DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_prt_token UNIQUE (token_hash),
    CONSTRAINT fk_prt_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    INDEX idx_prt_user (user_id)
) ENGINE=InnoDB;

INSERT INTO users (id, email, username, password_hash, full_name, avatar_url, system_role, is_active, last_login_at, created_at) VALUES
(1, 'admin@taskflow.vn',   'admin',     '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Quản Trị Hệ Thống', NULL, 'admin', TRUE,  '2026-11-04 07:45:00', '2026-08-20 09:00:00'),
(2, 'minh.tran@taskflow.vn', 'minhtran', '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Trần Quang Minh',    'https://i.pravatar.cc/150?img=11', 'user', TRUE,  '2026-11-04 08:10:00', '2026-08-25 10:00:00'),
(3, 'lan.pham@taskflow.vn',  'lanpham',  '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Phạm Thị Lan',      'https://i.pravatar.cc/150?img=32', 'user', TRUE,  '2026-11-04 08:30:00', '2026-08-25 10:15:00'),
(4, 'hung.le@taskflow.vn',   'hungle',   '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Lê Quốc Hùng',      'https://i.pravatar.cc/150?img=15', 'user', TRUE,  '2026-11-03 17:20:00', '2026-08-26 08:30:00'),
(5, 'thao.vu@taskflow.vn',   'thaovu',   '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Vũ Phương Thảo',    'https://i.pravatar.cc/150?img=47', 'user', TRUE,  '2026-11-04 09:05:00', '2026-08-27 14:00:00'),
(6, 'nam.do@taskflow.vn',    'namdo',    '$2b$12$o3mDxKlt8BBdedgZYRkwWuTyRSimL8FFwdrMubxELuvSSSFDgsKx.', 'Đỗ Hoàng Nam',      NULL,                               'user', FALSE, '2026-10-02 11:00:00', '2026-09-01 09:00:00');
 
INSERT INTO projects (id, name, description, owner_id, status, start_date, end_date, created_at) VALUES
(1, 'Xây dựng Website Thương mại điện tử', 'Phát triển website bán hàng trực tuyến gồm quản lý sản phẩm, giỏ hàng, thanh toán VNPay và quản trị đơn hàng.', 2, 'active',    '2026-09-01', '2026-12-31', '2026-09-01 08:00:00'),
(2, 'Ứng dụng Di động Quản lý Chi tiêu',   'Ứng dụng Flutter giúp ghi chép thu chi, thống kê theo tháng và nhắc nhở ngân sách.',                                        3, 'active',    '2026-10-01', '2027-02-28', '2026-10-01 09:00:00'),
(3, 'Chiến dịch Marketing Quý 3',           'Kế hoạch truyền thông và quảng cáo trực tuyến cho đợt khuyến mãi quý 3.',                                                    2, 'completed', '2026-07-01', '2026-09-30', '2026-07-01 08:30:00');
 
INSERT INTO project_members (project_id, user_id, role, joined_at) VALUES
(1, 2, 'owner',   '2026-09-01 08:00:00'),
(1, 3, 'manager', '2026-09-01 08:10:00'),
(1, 4, 'member',  '2026-09-01 08:15:00'),
(1, 5, 'member',  '2026-09-02 09:30:00'),
(1, 6, 'viewer',  '2026-09-05 10:00:00'),
(2, 3, 'owner',   '2026-10-01 09:00:00'),
(2, 2, 'member',  '2026-10-01 09:10:00'),
(2, 5, 'member',  '2026-10-01 09:20:00'),
(2, 4, 'viewer',  '2026-10-03 15:00:00'),
(3, 2, 'owner',   '2026-07-01 08:30:00'),
(3, 5, 'member',  '2026-07-01 08:40:00'),
(3, 4, 'member',  '2026-07-02 09:00:00');
 
INSERT INTO project_invitations (id, project_id, inviter_id, invitee_email, invitee_id, role, token, status, expires_at, created_at, responded_at) VALUES
(1, 1, 2, 'thao.vu@taskflow.vn',      5,    'member', '8725d63aae4082bc2ed532d570b7a44b6ae7519804ce86098ccab13628d142e8', 'accepted', '2026-09-09 09:00:00', '2026-09-02 09:00:00', '2026-09-02 09:30:00'),
(2, 1, 3, 'khach.moi@example.com',    NULL, 'viewer', 'd7066c8ea96e6c4ec0108dff12322fbe0c98beda55a084a57f7feb26db9d9245', 'pending',  '2026-11-15 09:00:00', '2026-11-01 09:00:00', NULL),
(3, 2, 3, 'hung.le@taskflow.vn',      4,    'viewer', '2807abc18ff35aa28b2385a2adc72bfd40b90c89efbe29b330ff843d97139069', 'accepted', '2026-10-10 09:00:00', '2026-10-03 14:30:00', '2026-10-03 15:00:00'),
(4, 2, 3, 'ctv.design@example.com',   NULL, 'member', 'b2d04ddec3ca17678eea9bbe128cd9b60a863584aa6393a101e0ff1f1e1029de', 'expired',  '2026-10-20 09:00:00', '2026-10-13 09:00:00', NULL);
 
INSERT INTO lists (id, project_id, name, position, is_done_column, created_at) VALUES
(1,  1, 'Backlog',     1, FALSE, '2026-09-01 08:20:00'),
(2,  1, 'Cần làm',     2, FALSE, '2026-09-01 08:20:00'),
(3,  1, 'Đang làm',    3, FALSE, '2026-09-01 08:20:00'),
(4,  1, 'Đang review', 4, FALSE, '2026-09-01 08:20:00'),
(5,  1, 'Hoàn thành',  5, TRUE,  '2026-09-01 08:20:00'),
(6,  2, 'Cần làm',     1, FALSE, '2026-10-01 09:30:00'),
(7,  2, 'Đang làm',    2, FALSE, '2026-10-01 09:30:00'),
(8,  2, 'Hoàn thành',  3, TRUE,  '2026-10-01 09:30:00'),
(9,  3, 'Cần làm',     1, FALSE, '2026-07-01 09:00:00'),
(10, 3, 'Đang làm',    2, FALSE, '2026-07-01 09:00:00'),
(11, 3, 'Hoàn thành',  3, TRUE,  '2026-07-01 09:00:00');
 
INSERT INTO tasks (id, project_id, list_id, title, description, position, priority, start_date, due_date, completed_at, created_by, created_at, deleted_at) VALUES
(1,  1, 5,  'Thiết kế cơ sở dữ liệu',                     'Thiết kế ERD, chuẩn hóa đến 3NF và viết script tạo bảng MySQL.',                          1, 'high',   '2026-09-02 08:00:00', '2026-09-10 17:00:00', '2026-09-09 10:30:00', 2, '2026-09-02 08:00:00', NULL),
(2,  1, 5,  'Thiết kế giao diện trang chủ',               'Hoàn thiện mockup trang chủ, trang danh mục và trang chi tiết sản phẩm.',                  2, 'medium', '2026-09-05 08:00:00', '2026-09-20 17:00:00', '2026-09-18 16:00:00', 3, '2026-09-05 08:30:00', NULL),
(3,  1, 5,  'Xây dựng API xác thực JWT',                  'Đăng ký, đăng nhập, làm mới token và phân quyền theo vai trò.',                            3, 'high',   '2026-09-10 08:00:00', '2026-09-25 17:00:00', '2026-09-24 15:20:00', 3, '2026-09-10 08:30:00', NULL),
(4,  1, 4,  'Xây dựng API sản phẩm và danh mục',          'CRUD sản phẩm, danh mục, phân trang và lọc theo giá, danh mục.',                           1, 'high',   '2026-10-01 08:00:00', '2026-10-20 17:00:00', NULL,                  3, '2026-10-01 08:30:00', NULL),
(5,  1, 3,  'Tích hợp cổng thanh toán VNPay',             'Tạo URL thanh toán, xử lý callback IPN và đối soát giao dịch.',                            1, 'urgent', '2026-10-15 08:00:00', '2026-11-10 17:00:00', NULL,                  2, '2026-10-15 08:30:00', NULL),
(6,  1, 3,  'Xây dựng chức năng giỏ hàng',                'Thêm, sửa, xóa sản phẩm trong giỏ và tính tổng tiền kèm khuyến mãi.',                      2, 'high',   '2026-10-20 08:00:00', '2026-11-12 17:00:00', NULL,                  3, '2026-10-20 09:00:00', NULL),
(7,  1, 2,  'Viết unit test cho module đơn hàng',         'Bao phủ tối thiểu 80% các service tạo đơn, hủy đơn và cập nhật trạng thái.',               1, 'medium', '2026-11-05 08:00:00', '2026-11-20 17:00:00', NULL,                  3, '2026-10-28 10:00:00', NULL),
(8,  1, 2,  'Tối ưu truy vấn danh sách sản phẩm',         'Phân tích EXPLAIN, bổ sung chỉ mục và giảm số truy vấn N+1.',                              2, 'medium', '2026-11-08 08:00:00', '2026-11-18 17:00:00', NULL,                  2, '2026-10-30 14:00:00', NULL),
(9,  1, 1,  'Tích hợp gửi email thông báo đơn hàng',      'Gửi email xác nhận đơn, giao hàng thành công qua hàng đợi nền.',                           1, 'low',    NULL,                  NULL,                  NULL,                  2, '2026-10-05 11:00:00', NULL),
(10, 1, 1,  'Triển khai lên máy chủ staging',             'Dockerize ứng dụng, cấu hình Nginx, HTTPS và biến môi trường.',                            2, 'high',   '2026-11-25 08:00:00', '2026-12-05 17:00:00', NULL,                  2, '2026-10-12 09:00:00', NULL),
(11, 1, 1,  'Nghiên cứu chatbot hỗ trợ khách hàng',       'Đánh giá khả năng tích hợp chatbot tư vấn sản phẩm.',                                      3, 'low',    NULL,                  NULL,                  NULL,                  2, '2026-10-06 09:00:00', '2026-10-25 16:00:00'),
(12, 2, 8,  'Phác thảo wireframe màn hình chính',         'Wireframe màn hình tổng quan, thêm giao dịch và thống kê.',                                1, 'medium', '2026-10-02 08:00:00', '2026-10-12 17:00:00', '2026-10-11 14:00:00', 3, '2026-10-02 08:30:00', NULL),
(13, 2, 8,  'Thiết lập dự án Flutter và CI/CD',           'Khởi tạo cấu trúc dự án, lint và pipeline build tự động.',                                 2, 'high',   '2026-10-05 08:00:00', '2026-10-15 17:00:00', '2026-10-14 11:00:00', 3, '2026-10-05 08:30:00', NULL),
(14, 2, 7,  'Màn hình thêm giao dịch',                    'Form nhập số tiền, danh mục, ngày và ghi chú cho giao dịch thu chi.',                      1, 'high',   '2026-10-20 08:00:00', '2026-11-08 17:00:00', NULL,                  3, '2026-10-20 09:00:00', NULL),
(15, 2, 7,  'Đồng bộ dữ liệu offline',                    'Lưu cục bộ bằng SQLite và đồng bộ lên máy chủ khi có mạng.',                               2, 'urgent', '2026-10-28 08:00:00', '2026-11-15 17:00:00', NULL,                  2, '2026-10-28 09:00:00', NULL),
(16, 2, 6,  'Biểu đồ thống kê chi tiêu theo tháng',       'Biểu đồ cột và tròn thể hiện chi tiêu theo danh mục từng tháng.',                          1, 'medium', '2026-11-10 08:00:00', '2026-11-30 17:00:00', NULL,                  3, '2026-10-25 10:00:00', NULL),
(17, 2, 6,  'Xuất báo cáo PDF',                           'Cho phép xuất báo cáo thu chi theo khoảng thời gian ra tệp PDF.',                          2, 'low',    '2026-12-01 08:00:00', '2026-12-15 17:00:00', NULL,                  3, '2026-10-25 10:30:00', NULL),
(18, 2, 6,  'Nhắc nhở khi vượt hạn mức ngân sách',        'Gửi thông báo đẩy khi tổng chi tiêu vượt hạn mức đã đặt.',                                 3, 'medium', NULL,                  NULL,                  NULL,                  5, '2026-10-26 15:00:00', NULL),
(19, 3, 11, 'Lên kế hoạch nội dung truyền thông',         'Xây dựng lịch đăng bài, thông điệp chính và bộ nhận diện cho chiến dịch.',                 1, 'high',   '2026-07-01 08:00:00', '2026-07-15 17:00:00', '2026-07-14 16:30:00', 2, '2026-07-01 09:00:00', NULL),
(20, 3, 11, 'Chạy quảng cáo Facebook Ads',                'Thiết lập chiến dịch, tối ưu đối tượng và theo dõi chuyển đổi hằng tuần.',                 2, 'high',   '2026-07-20 08:00:00', '2026-09-15 17:00:00', '2026-09-16 17:00:00', 2, '2026-07-18 09:00:00', NULL),
(21, 3, 11, 'Tổng kết báo cáo chiến dịch',                'Tổng hợp chỉ số CPC, CTR, doanh thu và bài học kinh nghiệm.',                              3, 'medium', '2026-09-20 08:00:00', '2026-09-30 17:00:00', '2026-09-29 15:00:00', 5, '2026-09-18 10:00:00', NULL);
 
INSERT INTO task_assignees (task_id, user_id, assigned_by, assigned_at) VALUES
(1,  3, 2, '2026-09-02 08:05:00'),
(1,  4, 2, '2026-09-02 08:05:00'),
(2,  5, 3, '2026-09-05 08:40:00'),
(3,  4, 3, '2026-09-10 08:40:00'),
(4,  4, 3, '2026-10-01 08:40:00'),
(4,  5, 3, '2026-10-01 08:40:00'),
(5,  3, 2, '2026-10-15 08:40:00'),
(5,  4, 2, '2026-10-15 08:40:00'),
(6,  5, 3, '2026-10-20 09:10:00'),
(7,  4, 3, '2026-10-28 10:10:00'),
(8,  3, 2, '2026-10-30 14:10:00'),
(9,  5, 2, '2026-10-05 11:10:00'),
(10, 3, 2, '2026-10-12 09:10:00'),
(10, 4, 2, '2026-10-12 09:10:00'),
(11, 2, 2, '2026-10-06 09:05:00'),
(12, 5, 3, '2026-10-02 08:40:00'),
(13, 3, 3, '2026-10-05 08:40:00'),
(14, 2, 3, '2026-10-20 09:10:00'),
(14, 5, 3, '2026-10-20 09:10:00'),
(15, 2, 3, '2026-10-28 09:10:00'),
(15, 5, 3, '2026-10-28 09:10:00'),
(16, 5, 3, '2026-10-25 10:10:00'),
(17, 2, 3, '2026-10-25 10:40:00'),
(18, 5, 3, '2026-10-26 15:10:00'),
(19, 5, 2, '2026-07-01 09:10:00'),
(20, 4, 2, '2026-07-18 09:10:00'),
(20, 5, 2, '2026-07-18 09:10:00'),
(21, 5, 2, '2026-09-18 10:10:00');
 
INSERT INTO comments (id, task_id, user_id, parent_id, content, created_at, deleted_at) VALUES
(1,  5,  3, NULL, 'Đã có tài khoản sandbox của VNPay, mình sẽ gửi thông tin cấu hình qua email nội bộ.',                         '2026-10-16 09:15:00', NULL),
(2,  5,  2, 1,    '@lanpham OK, nhớ lưu khóa trong biến môi trường, không commit lên repo nhé.',                                '2026-10-16 09:40:00', NULL),
(3,  5,  4, NULL, 'Phần callback IPN cần kiểm tra chữ ký HMAC SHA512, mình sẽ làm trước phần này.',                              '2026-10-18 14:20:00', NULL),
(4,  4,  3, NULL, 'API đã xong, nhờ Hùng review giúp phần phân trang và lọc theo danh mục.',                                     '2026-10-30 16:00:00', NULL),
(5,  4,  4, 4,    'Mình review xong, cần bổ sung chỉ mục cho cột category_id để truy vấn nhanh hơn.',                            '2026-10-31 10:30:00', NULL),
(6,  6,  5, NULL, 'Giỏ hàng nên lưu theo người dùng hay theo phiên cho khách chưa đăng nhập?',                                   '2026-10-22 11:00:00', NULL),
(7,  6,  3, 6,    'Lưu theo người dùng, khách chưa đăng nhập dùng localStorage rồi gộp vào giỏ khi đăng nhập.',                  '2026-10-22 13:30:00', NULL),
(8,  15, 2, NULL, 'Dùng SQLite cục bộ và đồng bộ theo cơ chế last-write-wins được không?',                                       '2026-10-29 10:00:00', NULL),
(9,  15, 3, 8,    'Được, nhưng cần lưu thêm updated_at cho từng bản ghi để xử lý xung đột.',                                     '2026-10-29 11:15:00', NULL),
(10, 14, 5, NULL, 'Đã xong giao diện form, còn phần kiểm tra hợp lệ số tiền.',                                                   '2026-11-02 17:00:00', NULL),
(11, 20, 2, NULL, 'Ngân sách quảng cáo vượt 5% so với kế hoạch, cần giải trình trong báo cáo tổng kết.',                         '2026-09-16 17:30:00', NULL),
(12, 1,  4, NULL, 'Đã chuẩn hóa đến 3NF, xem sơ đồ ERD đính kèm.',                                                               '2026-09-09 10:00:00', NULL),
(13, 5,  4, NULL, 'Bình luận đã được xóa bởi tác giả.',                                                                          '2026-10-19 08:00:00', '2026-10-19 08:10:00');
 
INSERT INTO labels (id, project_id, name, color, created_at) VALUES
(1, 1, 'Backend',    '#2563EB', '2026-09-01 08:25:00'),
(2, 1, 'Frontend',   '#16A34A', '2026-09-01 08:25:00'),
(3, 1, 'Bug',        '#DC2626', '2026-09-01 08:25:00'),
(4, 1, 'Thanh toán', '#F59E0B', '2026-09-01 08:25:00'),
(5, 2, 'Mobile',     '#7C3AED', '2026-10-01 09:35:00'),
(6, 2, 'UI/UX',      '#EC4899', '2026-10-01 09:35:00'),
(7, 2, 'Bug',        '#DC2626', '2026-10-01 09:35:00'),
(8, 3, 'Nội dung',   '#0EA5E9', '2026-07-01 09:05:00'),
(9, 3, 'Quảng cáo',  '#F97316', '2026-07-01 09:05:00');
 
INSERT INTO task_labels (task_id, label_id) VALUES
(1, 1), (2, 2), (3, 1), (4, 1), (5, 1), (5, 4), (6, 1), (6, 2), (7, 1), (8, 1), (9, 1), (10, 1),
(12, 6), (13, 5), (14, 5), (14, 6), (15, 5), (16, 5), (16, 6), (17, 5), (18, 5),
(19, 8), (20, 9), (21, 8);
 
INSERT INTO checklist_items (task_id, content, is_done, position, completed_at, created_at) VALUES
(5,  'Đăng ký tài khoản sandbox VNPay',        TRUE,  1, '2026-10-16 09:00:00', '2026-10-15 09:00:00'),
(5,  'Cấu hình mã đơn vị và khóa bí mật',      TRUE,  2, '2026-10-17 10:00:00', '2026-10-15 09:00:00'),
(5,  'Tạo URL thanh toán',                      TRUE,  3, '2026-10-20 15:00:00', '2026-10-15 09:00:00'),
(5,  'Xử lý callback IPN',                      FALSE, 4, NULL,                  '2026-10-15 09:00:00'),
(5,  'Kiểm thử luồng hoàn tiền',                FALSE, 5, NULL,                  '2026-10-15 09:00:00'),
(6,  'Thêm sản phẩm vào giỏ',                   TRUE,  1, '2026-10-25 11:00:00', '2026-10-20 09:30:00'),
(6,  'Cập nhật số lượng',                       TRUE,  2, '2026-10-28 16:00:00', '2026-10-20 09:30:00'),
(6,  'Xóa sản phẩm khỏi giỏ',                   FALSE, 3, NULL,                  '2026-10-20 09:30:00'),
(6,  'Tính tổng tiền và khuyến mãi',            FALSE, 4, NULL,                  '2026-10-20 09:30:00'),
(10, 'Cấu hình Docker Compose',                 FALSE, 1, NULL,                  '2026-10-12 09:30:00'),
(10, 'Thiết lập biến môi trường',               FALSE, 2, NULL,                  '2026-10-12 09:30:00'),
(10, 'Cấu hình Nginx và HTTPS',                 FALSE, 3, NULL,                  '2026-10-12 09:30:00'),
(14, 'Hoàn thiện giao diện form',               TRUE,  1, '2026-11-02 16:30:00', '2026-10-20 09:30:00'),
(14, 'Kiểm tra hợp lệ số tiền',                 FALSE, 2, NULL,                  '2026-10-20 09:30:00'),
(14, 'Chọn danh mục và ngày giao dịch',         FALSE, 3, NULL,                  '2026-10-20 09:30:00'),
(20, 'Tạo tài khoản quảng cáo',                 TRUE,  1, '2026-07-20 10:00:00', '2026-07-18 09:30:00'),
(20, 'Thiết lập đối tượng mục tiêu',            TRUE,  2, '2026-07-22 15:00:00', '2026-07-18 09:30:00'),
(20, 'Theo dõi chuyển đổi hằng tuần',           TRUE,  3, '2026-09-15 17:00:00', '2026-07-18 09:30:00');
 
INSERT INTO attachments (id, task_id, comment_id, uploaded_by, file_name, file_path, file_size, mime_type, created_at) VALUES
(1, 1,  12,   4, 'erd_taskflow_v2.png',       '/uploads/projects/1/tasks/1/erd_taskflow_v2.png',       245760,  'image/png',                                                              '2026-09-09 10:00:00'),
(2, 5,  NULL, 3, 'vnpay_sandbox_guide.pdf',   '/uploads/projects/1/tasks/5/vnpay_sandbox_guide.pdf',   1048576, 'application/pdf',                                                        '2026-10-16 09:10:00'),
(3, 12, NULL, 5, 'wireframe_home.png',        '/uploads/projects/2/tasks/12/wireframe_home.png',       512000,  'image/png',                                                              '2026-10-11 13:50:00'),
(4, 20, NULL, 2, 'bao_cao_chi_phi_ads.xlsx',  '/uploads/projects/3/tasks/20/bao_cao_chi_phi_ads.xlsx', 87040,   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '2026-09-16 17:20:00'),
(5, 21, NULL, 5, 'bao_cao_tong_ket_q3.pdf',   '/uploads/projects/3/tasks/21/bao_cao_tong_ket_q3.pdf',  2097152, 'application/pdf',                                                        '2026-09-29 14:50:00');
 
INSERT INTO notifications (id, user_id, actor_id, project_id, task_id, type, message, is_read, read_at, created_at) VALUES
(1,  3, 2,    1, 5,    'task_assigned',   'Trần Quang Minh đã giao cho bạn công việc «Tích hợp cổng thanh toán VNPay».',        TRUE,  '2026-10-15 09:00:00', '2026-10-15 08:40:00'),
(2,  4, 2,    1, 5,    'task_assigned',   'Trần Quang Minh đã giao cho bạn công việc «Tích hợp cổng thanh toán VNPay».',        TRUE,  '2026-10-15 10:00:00', '2026-10-15 08:40:00'),
(3,  2, 3,    1, 5,    'comment_added',   'Phạm Thị Lan đã bình luận trong «Tích hợp cổng thanh toán VNPay».',                  FALSE, NULL,                  '2026-10-16 09:15:00'),
(4,  3, 2,    1, 5,    'mentioned',       'Trần Quang Minh đã nhắc đến bạn trong «Tích hợp cổng thanh toán VNPay».',            TRUE,  '2026-10-16 10:00:00', '2026-10-16 09:40:00'),
(5,  3, 4,    1, 4,    'comment_added',   'Lê Quốc Hùng đã bình luận trong «Xây dựng API sản phẩm và danh mục».',               FALSE, NULL,                  '2026-10-31 10:30:00'),
(6,  5, 3,    1, 6,    'comment_added',   'Phạm Thị Lan đã trả lời bình luận của bạn trong «Xây dựng chức năng giỏ hàng».',     FALSE, NULL,                  '2026-10-22 13:30:00'),
(7,  2, NULL, 2, 14,   'task_due_soon',   'Công việc «Màn hình thêm giao dịch» sẽ đến hạn vào 08/11/2026.',                     FALSE, NULL,                  '2026-11-04 08:00:00'),
(8,  5, NULL, 2, 14,   'task_due_soon',   'Công việc «Màn hình thêm giao dịch» sẽ đến hạn vào 08/11/2026.',                     FALSE, NULL,                  '2026-11-04 08:00:00'),
(9,  3, NULL, 1, 5,    'task_due_soon',   'Công việc «Tích hợp cổng thanh toán VNPay» sẽ đến hạn vào 10/11/2026.',              FALSE, NULL,                  '2026-11-04 08:00:00'),
(10, 4, 3,    2, NULL, 'project_invited', 'Phạm Thị Lan đã mời bạn tham gia dự án «Ứng dụng Di động Quản lý Chi tiêu».',        TRUE,  '2026-10-03 15:00:00', '2026-10-03 14:30:00'),
(11, 2, 5,    1, NULL, 'member_joined',   'Vũ Phương Thảo đã tham gia dự án «Xây dựng Website Thương mại điện tử».',            TRUE,  '2026-09-02 10:00:00', '2026-09-02 09:30:00'),
(12, 2, 5,    3, 21,   'task_completed',  'Vũ Phương Thảo đã hoàn thành công việc «Tổng kết báo cáo chiến dịch».',              TRUE,  '2026-09-29 16:00:00', '2026-09-29 15:00:00');
 
INSERT INTO activity_logs (id, project_id, task_id, user_id, entity_type, entity_id, action, old_value, new_value, created_at) VALUES
(1,  1, NULL, 2, 'project',    1,  'created',          NULL,                                  '{"name": "Xây dựng Website Thương mại điện tử"}',                  '2026-09-01 08:00:00'),
(2,  1, NULL, 2, 'member',     3,  'member_added',     NULL,                                  '{"user_id": 3, "role": "manager"}',                                '2026-09-01 08:10:00'),
(3,  1, 1,    2, 'task',       1,  'created',          NULL,                                  '{"title": "Thiết kế cơ sở dữ liệu", "priority": "high"}',          '2026-09-02 08:00:00'),
(4,  1, 1,    4, 'attachment', 1,  'uploaded',         NULL,                                  '{"file_name": "erd_taskflow_v2.png"}',                             '2026-09-09 10:00:00'),
(5,  1, 1,    3, 'task',       1,  'moved',            '{"list_id": 3}',                      '{"list_id": 5}',                                                   '2026-09-09 10:30:00'),
(6,  1, 5,    2, 'task',       5,  'assignee_added',   NULL,                                  '{"user_id": 3}',                                                   '2026-10-15 08:40:00'),
(7,  1, 5,    2, 'task',       5,  'priority_changed', '{"priority": "high"}',                '{"priority": "urgent"}',                                           '2026-10-16 08:00:00'),
(8,  1, 5,    3, 'comment',    1,  'created',          NULL,                                  '{"task_id": 5}',                                                   '2026-10-16 09:15:00'),
(9,  1, 11,   2, 'task',       11, 'deleted',          NULL,                                  '{"title": "Nghiên cứu chatbot hỗ trợ khách hàng"}',                '2026-10-25 16:00:00'),
(10, 1, 4,    3, 'task',       4,  'moved',            '{"list_id": 3}',                      '{"list_id": 4}',                                                   '2026-10-30 16:00:00'),
(11, 1, NULL, 3, 'invitation', 2,  'invitation_sent',  NULL,                                  '{"email": "khach.moi@example.com", "role": "viewer"}',             '2026-11-01 09:00:00'),
(12, 2, NULL, 3, 'project',    2,  'created',          NULL,                                  '{"name": "Ứng dụng Di động Quản lý Chi tiêu"}',                    '2026-10-01 09:00:00'),
(13, 2, 13,   3, 'task',       13, 'moved',            '{"list_id": 7}',                      '{"list_id": 8}',                                                   '2026-10-14 11:00:00'),
(14, 2, 15,   2, 'task',       15, 'due_date_changed', '{"due_date": "2026-11-10 17:00:00"}', '{"due_date": "2026-11-15 17:00:00"}',                              '2026-10-30 09:00:00'),
(15, 3, 20,   2, 'task',       20, 'completed',        '{"completed_at": null}',              '{"completed_at": "2026-09-16 17:00:00"}',                          '2026-09-16 17:00:00'),
(16, 3, NULL, 2, 'project',    3,  'status_changed',   '{"status": "active"}',                '{"status": "completed"}',                                          '2026-10-01 09:00:00');
 
INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at, used_at, created_at) VALUES
(1, 4, '8a41b6383ed95741a684274ed5a831502192cab0abf77e47716c0ea3c8738581', '2026-10-10 09:00:00', '2026-10-09 21:15:00', '2026-10-09 20:50:00'),
(2, 5, '7667b3310f82aaa111849aa49982c3d19cfd7f7387078adf7c758c494100c159', '2026-11-05 09:00:00', NULL,                  '2026-11-04 09:00:00');
 