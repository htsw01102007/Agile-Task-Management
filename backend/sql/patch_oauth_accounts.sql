-- Liên kết tài khoản Google / Facebook. Không lưu access token hay client secret.
USE task_project_management;

CREATE TABLE IF NOT EXISTS oauth_accounts (
    id                BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id           BIGINT UNSIGNED NOT NULL,
    provider          ENUM('GOOGLE', 'FACEBOOK') NOT NULL,
    provider_user_id  VARCHAR(255) NOT NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_oauth_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT uq_oauth_provider_user UNIQUE (provider, provider_user_id),
    INDEX idx_oauth_user (user_id)
) ENGINE=InnoDB;
