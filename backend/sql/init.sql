-- Tạo database app_db + bảng items + dữ liệu mẫu.
-- Cách chạy bằng MySQL Workbench:
--   File > Open SQL Script... > chọn file này > bấm nút tia sét (Execute) > Refresh ô SCHEMAS.
-- Chạy lại nhiều lần không lỗi (đã có thì bỏ qua), chỉ là dữ liệu mẫu sẽ bị thêm lặp.

SET NAMES utf8mb4; -- để tiếng Việt không bị lỗi font

CREATE DATABASE IF NOT EXISTS app_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE app_db;

CREATE TABLE IF NOT EXISTS items (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(255) NOT NULL,
  description TEXT NULL,
  price       DECIMAL(12, 2) NOT NULL DEFAULT 0,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO items (name, description, price) VALUES
  ('Cơm rang dưa bò', 'Món mẫu để kiểm tra API', 45000),
  ('Trà đá', 'Dữ liệu mẫu số 2', 5000);

-- ---------------------------------------------------------------
-- Dữ liệu mẫu cho chức năng CRUD lists (cột công việc trong project)
-- Đăng nhập mẫu (header X-User-Id): dùng id thật của user sau khi INSERT.
-- Xem id bằng: SELECT id, full_name FROM users;
-- Tài khoản mẫu: An (owner), Bình (manager), Chi (member), Dũng (viewer)
-- Chạy lại script này sẽ INSERT lặp -> nếu đã chạy rồi thì bỏ qua phần dưới.
-- ---------------------------------------------------------------
INSERT INTO users (email, password_hash, full_name) VALUES
  ('an@example.com', 'hash1', 'An (owner)'),
  ('binh@example.com', 'hash2', 'Bình (manager)'),
  ('chi@example.com', 'hash3', 'Chi (member)'),
  ('dung@example.com', 'hash4', 'Dũng (viewer)');

INSERT INTO users (email, password_hash, full_name, is_active) VALUES
  ('an@example.com', 'hash1', 'An (owner)', 1),
  ('binh@example.com', 'hash2', 'Bình (manager)', 1),
  ('chi@example.com', 'hash3', 'Chi (member)', 1),
  ('dung@example.com', 'hash4', 'Dũng (viewer)', 1);

INSERT INTO projects (name, description, owner_id, is_archived) VALUES
  ('Dự án mẫu', 'Project demo cho CRUD lists',
   (SELECT id FROM users WHERE email = 'an@example.com'), 0);

INSERT INTO project_members (project_id, user_id, role)
SELECT p.id, u.id, r.role FROM projects p, users u JOIN (
  SELECT 'an@example.com' AS email, 'owner' AS role
  UNION SELECT 'binh@example.com', 'manager'
  UNION SELECT 'chi@example.com', 'member'
  UNION SELECT 'dung@example.com', 'viewer'
) r ON r.email = u.email WHERE p.name = 'Dự án mẫu';

INSERT INTO lists (project_id, name, position, is_done_column)
SELECT p.id, c.name, c.pos, c.done FROM projects p JOIN (
  SELECT 'Việc cần làm' AS name, 1 AS pos, 0 AS done
  UNION SELECT 'Đang làm', 2, 0
  UNION SELECT 'Hoàn thành', 3, 1
) c WHERE p.name = 'Dự án mẫu';
