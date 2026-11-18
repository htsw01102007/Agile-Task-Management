from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


NOTIFICATION_TYPES = (
    "task_created",
    "task_assigned",
    "task_updated",
    "task_moved",
    "task_completed",
    "task_deleted",
    "task_overdue",
    "task_due_soon",
    "comment_added",
    "comment_updated",
    "comment_deleted",
    "invitation_sent",
    "invitation_accepted",
    "invitation_declined",
    "member_added",
    "member_removed",
    "member_role_changed",
    "project_updated",
    "deadline_reminder",
    "mentioned",
    "project_invited",
    "member_joined",
)


def upgrade_notification_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("notifications"):
        return

    columns = {column["name"]: column for column in inspector.get_columns("notifications")}
    with engine.begin() as connection:
        if "title" not in columns:
            connection.execute(text("ALTER TABLE notifications ADD COLUMN title VARCHAR(255) NULL"))
            connection.execute(
                text("UPDATE notifications SET title = LEFT(COALESCE(message, ''), 255) WHERE title IS NULL")
            )
            connection.execute(text("ALTER TABLE notifications MODIFY COLUMN title VARCHAR(255) NOT NULL"))
        elif columns["title"]["nullable"]:
            connection.execute(
                text("UPDATE notifications SET title = LEFT(COALESCE(message, ''), 255) WHERE title IS NULL")
            )
            connection.execute(text("ALTER TABLE notifications MODIFY COLUMN title VARCHAR(255) NOT NULL"))

        if "entity_type" not in columns:
            connection.execute(text("ALTER TABLE notifications ADD COLUMN entity_type VARCHAR(50) NULL"))
        if "entity_id" not in columns:
            connection.execute(text("ALTER TABLE notifications ADD COLUMN entity_id BIGINT NULL"))

        notification_type = columns["type"]["type"]
        existing_values = getattr(notification_type, "enums", None)
        if existing_values is not None:
            enum_values = list(dict.fromkeys((*existing_values, *NOTIFICATION_TYPES)))
            if enum_values != list(existing_values):
                escaped_values = [value.replace("'", "''") for value in enum_values]
                values_sql = ", ".join(f"'{value}'" for value in escaped_values)
                connection.execute(
                    text(f"ALTER TABLE notifications MODIFY COLUMN type ENUM({values_sql}) NOT NULL")
                )
