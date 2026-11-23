"""sync schema: đưa DB cũ (sql/init.sql) về đúng với các model hiện tại

Migration này được viết tay (KHÔNG dùng autogenerate) và chỉ thêm / nới lỏng:
  - không DROP bảng, không DROP cột, không DROP index  -> không mất dữ liệu
  - idempotent: chạy lại, hoặc chạy trên DB đã có sẵn cột, đều không lỗi

Revision ID: 7c1e5a0d2b41
Revises:
Create Date: 2026-11-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "7c1e5a0d2b41"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Kiểu id của DB tạo từ init.sql là BIGINT UNSIGNED -> cột FK mới phải cùng kiểu
UBIGINT = mysql.BIGINT(unsigned=True)

NOTIFICATION_TYPES = (
    # giá trị cũ trong init.sql (giữ lại để dữ liệu cũ không bị lỗi)
    "task_assigned", "task_due_soon", "task_overdue", "comment_added",
    "mentioned", "project_invited", "member_joined", "task_completed",
    # giá trị mới mà model Notification đang dùng
    "task_created", "task_updated", "task_moved", "task_deleted",
    "comment_updated", "comment_deleted",
    "invitation_sent", "invitation_accepted", "invitation_declined",
    "member_added", "member_removed", "member_role_changed",
    "project_updated", "deadline_reminder",
)


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return _inspector().has_table(name)


def _columns(table: str) -> set[str]:
    return {c["name"] for c in _inspector().get_columns(table)}


def _fk_names(table: str) -> set[str]:
    return {fk["name"] for fk in _inspector().get_foreign_keys(table) if fk.get("name")}


def upgrade() -> None:
    # ------------------------------------------------------------------ users
    if _has_table("users"):
        cols = _columns("users")
        if "token_version" not in cols:
            op.add_column(
                "users",
                sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
            )
        # Tài khoản đăng nhập Google không có mật khẩu
        op.execute("ALTER TABLE users MODIFY password_hash VARCHAR(255) NULL")

    # ------------------------------------------------------------------ tasks
    if _has_table("tasks"):
        cols = _columns("tasks")
        if "is_deleted" not in cols:
            op.add_column(
                "tasks",
                sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            )
            # Task đã xóa mềm bằng deleted_at ở schema cũ thì coi là đã xóa
            op.execute("UPDATE tasks SET is_deleted = 1 WHERE deleted_at IS NOT NULL")
            op.create_index("ix_tasks_is_deleted", "tasks", ["is_deleted"])
        if "deleted_at" not in cols:
            op.add_column("tasks", sa.Column("deleted_at", sa.DateTime(), nullable=True))
        op.execute("ALTER TABLE tasks MODIFY title VARCHAR(500) NOT NULL")

    # ---------------------------------------------------------- notifications
    if _has_table("notifications"):
        cols = _columns("notifications")
        if "title" not in cols:
            op.add_column(
                "notifications",
                sa.Column("title", sa.String(255), nullable=False, server_default=""),
            )
            # Dữ liệu cũ chỉ có message -> dùng message làm tiêu đề
            op.execute("UPDATE notifications SET title = LEFT(message, 255) WHERE title = ''")
        if "entity_type" not in cols:
            op.add_column("notifications", sa.Column("entity_type", sa.String(50), nullable=True))
        if "entity_id" not in cols:
            op.add_column("notifications", sa.Column("entity_id", UBIGINT, nullable=True))
            op.create_index("ix_notifications_entity_id", "notifications", ["entity_id"])
            if "task_id" in cols:
                op.execute(
                    "UPDATE notifications SET entity_type = 'task', entity_id = task_id "
                    "WHERE task_id IS NOT NULL"
                )
        enum_sql = ", ".join(f"'{v}'" for v in NOTIFICATION_TYPES)
        op.execute(f"ALTER TABLE notifications MODIFY type ENUM({enum_sql}) NOT NULL")
        op.execute("ALTER TABLE notifications MODIFY message TEXT NULL")

    # ------------------------------------------------------------ attachments
    if _has_table("attachments"):
        cols = _columns("attachments")
        if "user_id" not in cols:
            op.add_column("attachments", sa.Column("user_id", UBIGINT, nullable=True))
            if "uploaded_by" in cols:
                op.execute("UPDATE attachments SET user_id = uploaded_by WHERE uploaded_by IS NOT NULL")
            op.create_foreign_key(
                "fk_attachments_user_id", "attachments", "users", ["user_id"], ["id"],
                ondelete="CASCADE",
            )
        op.execute("ALTER TABLE attachments MODIFY mime_type VARCHAR(100) NULL")

    # ---------------------------------------------------------- activity_logs
    if _has_table("activity_logs"):
        op.execute("ALTER TABLE activity_logs MODIFY entity_type VARCHAR(50) NOT NULL")
        op.execute("ALTER TABLE activity_logs MODIFY entity_id BIGINT UNSIGNED NULL")

    # ------------------------------------------------------ project_invitations
    if _has_table("project_invitations") and "fk_inv_inviter" in _fk_names("project_invitations"):
        # Model cho phép inviter_id NULL + ON DELETE SET NULL
        op.execute("ALTER TABLE project_invitations DROP FOREIGN KEY fk_inv_inviter")
        op.execute("ALTER TABLE project_invitations MODIFY inviter_id BIGINT UNSIGNED NULL")
        op.execute(
            "ALTER TABLE project_invitations ADD CONSTRAINT fk_inv_inviter "
            "FOREIGN KEY (inviter_id) REFERENCES users (id) ON DELETE SET NULL"
        )

    # ------------------------------------------------- bảng còn thiếu hoàn toàn
    # (tự tạo ở đây để cột FK là BIGINT UNSIGNED, khớp với users.id của init.sql;
    #  nếu để create_all tạo thì MySQL báo lỗi FK không tương thích kiểu)
    if _has_table("users") and not _has_table("oauth_accounts"):
        op.create_table(
            "oauth_accounts",
            sa.Column("id", UBIGINT, primary_key=True, autoincrement=True),
            sa.Column("user_id", UBIGINT, nullable=False),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("provider_user_id", sa.String(255), nullable=False),
            sa.Column("access_token", sa.Text(), nullable=True),
            sa.Column("refresh_token", sa.Text(), nullable=True),
            sa.Column("token_expires_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
        )
        op.create_index("ix_oauth_accounts_user_id", "oauth_accounts", ["user_id"])

    if not _has_table("revoked_tokens"):
        op.create_table(
            "revoked_tokens",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("jti", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_revoked_tokens_id", "revoked_tokens", ["id"])
        op.create_index("ix_revoked_tokens_jti", "revoked_tokens", ["jti"], unique=True)


def downgrade() -> None:
    # Migration chỉ thêm/nới lỏng nên cố ý không có downgrade:
    # thu hẹp lại có thể làm mất dữ liệu đã ghi bằng schema mới.
    pass
