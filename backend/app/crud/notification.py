"""Tạo thông báo. Hàm này chỉ thêm vào session, không tự commit."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.entities import Task, User
from app.models.notification import Notification
from app.models.notification_enums import NotificationType
from app.models.task_assignee import TaskAssignee


def notify_task_assignees_about_comment(
    db: Session,
    *,
    task: Task,
    actor: User,
    parent: Comment | None,
) -> None:
    assignee_ids = list(
        db.scalars(select(TaskAssignee.user_id).where(TaskAssignee.task_id == task.id))
    )
    for user_id in assignee_ids:
        if user_id == actor.id:
            continue
        if parent is not None and parent.user_id == user_id:
            message = (
                f"{actor.full_name} đã trả lời bình luận của bạn trong «{task.title}»."
            )
        else:
            message = f"{actor.full_name} đã bình luận trong «{task.title}»."
        db.add(
            Notification(
                user_id=user_id,
                actor_id=actor.id,
                project_id=task.project_id,
                task_id=task.id,
                type=NotificationType.COMMENT_ADDED,
                message=message[:500],
                is_read=False,
            )
        )
