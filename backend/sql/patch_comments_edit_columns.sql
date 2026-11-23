-- Chạy file này nếu database đã tạo từ bản SQL cũ, thiếu cột sửa / xoá mềm bình luận.
-- Bản task_project_management.sql hiện tại đã có sẵn hai cột này khi tạo mới.
USE task_project_management;

ALTER TABLE comments
    ADD COLUMN edited_at DATETIME NULL AFTER content,
    ADD COLUMN deleted_by BIGINT UNSIGNED NULL AFTER deleted_at,
    ADD CONSTRAINT fk_comments_deleted_by FOREIGN KEY (deleted_by) REFERENCES users (id) ON DELETE SET NULL;
