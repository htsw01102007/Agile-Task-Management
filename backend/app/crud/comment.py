"""Đọc / ghi bình luận của task."""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.crud.notification import notify_task_assignees_about_comment
from app.models.comment import Comment
from app.models.entities import Task, User
from app.schemas.comment import CommentCreate


class CommentActionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def get_visible_task(db: Session, task_id: int) -> Task | None:
    task = db.get(Task, task_id)
    if task is None or task.deleted_at is not None:
        return None
    return task


def get_comment(db: Session, comment_id: int) -> Comment | None:
    query = (
        select(Comment)
        .where(Comment.id == comment_id)
        .options(
            selectinload(Comment.author),
            selectinload(Comment.replies).selectinload(Comment.author),
        )
    )
    return db.scalars(query).one_or_none()


def list_task_comments(db: Session, task_id: int) -> list[Comment]:
    query = (
        select(Comment)
        .where(Comment.task_id == task_id, Comment.parent_id.is_(None))
        .options(
            selectinload(Comment.author),
            selectinload(Comment.replies).selectinload(Comment.author),
        )
        .order_by(Comment.created_at, Comment.id)
    )
    return list(db.scalars(query))


def create_comment(db: Session, task: Task, author: User, data: CommentCreate) -> Comment:
    parent = None
    if data.parent_id is not None:
        parent = db.get(Comment, data.parent_id)
        if parent is None:
            raise CommentActionError("parent_not_found")
        if parent.task_id != task.id:
            raise CommentActionError("parent_other_task")
        if parent.parent_id is not None:
            raise CommentActionError("reply_to_reply")
        if parent.deleted_at is not None:
            raise CommentActionError("parent_deleted")

    comment = Comment(
        task_id=task.id,
        user_id=author.id,
        parent_id=data.parent_id,
        content=data.content,
    )
    db.add(comment)
    db.flush()
    notify_task_assignees_about_comment(db, task=task, actor=author, parent=parent)
    db.commit()
    loaded = get_comment(db, comment.id)
    if loaded is None:
        raise CommentActionError("missing_after_create")
    return loaded


def update_own_comment(db: Session, comment: Comment, content: str) -> Comment:
    comment.edit(content)
    db.commit()
    loaded = get_comment(db, comment.id)
    if loaded is None:
        raise CommentActionError("missing_after_update")
    return loaded


def soft_delete_own_comment(db: Session, comment: Comment, deleted_by_id: int) -> Comment:
    comment.soft_delete(deleted_by_id)
    db.commit()
    loaded = get_comment(db, comment.id)
    if loaded is None:
        raise CommentActionError("missing_after_delete")
    return loaded
