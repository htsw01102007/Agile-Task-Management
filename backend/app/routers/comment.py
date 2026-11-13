import json
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Set

from app.db.session import get_db
from app.core.permissions import get_task_and_membership, get_task_with_write_check
from app.core.ws_manager import notify_project_sync, notify_user_sync
from app.models.comment import Comment
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse

router = APIRouter(prefix="/projects/{project_id}/tasks/{task_id}/comments", tags=["Comments"])

MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_.+-]+(?:@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+)?)")


def _extract_mentioned_member_ids(db: Session, project_id: int, content: str, exclude_user_id: int) -> Set[int]:
    """Tìm các thành viên trong dự án được nhắc tên bằng @username / @email trong bình luận"""
    matches = {m.lower() for m in MENTION_PATTERN.findall(content or "")}
    if not matches:
        return set()

    members = (
        db.query(ProjectMember)
        .join(User, User.id == ProjectMember.user_id)
        .filter(ProjectMember.project_id == project_id)
        .all()
    )
    mentioned_ids: Set[int] = set()
    for pm in members:
        if pm.user_id == exclude_user_id or not pm.user:
            continue
        email_lower = (pm.user.email or "").lower()
        email_prefix = email_lower.split("@")[0] if "@" in email_lower else email_lower
        full_name_slug = (pm.user.full_name or "").lower().replace(" ", "")
        full_name_underscored = (pm.user.full_name or "").lower().replace(" ", "_")
        candidates = {email_lower, email_prefix, full_name_slug, full_name_underscored}
        if matches & candidates:
            mentioned_ids.add(pm.user_id)
    return mentioned_ids


@router.get("", response_model=List[CommentResponse])
def list_comments(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_and_membership),
):
    """Danh sách bình luận của task (sắp xếp theo thời gian tạo)"""
    task, member = data
    comments = (
        db.query(Comment)
        .filter(Comment.task_id == task_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .all()
    )

    result = []
    for c in comments:
        result.append(CommentResponse(
            id=c.id,
            task_id=c.task_id,
            user_id=c.user_id,
            content=c.content,
            created_at=c.created_at,
            updated_at=c.updated_at,
            user_email=c.user.email if c.user else None,
            user_full_name=c.user.full_name if c.user else None,
            user_avatar_url=c.user.avatar_url if c.user else None,
        ))
    return result


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    project_id: int,
    task_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Tạo bình luận mới trên task (hỗ trợ nhắc tên @username gửi thông báo)"""
    task, member = data

    comment = Comment(
        task_id=task_id,
        user_id=member.user_id,
        content=comment_in.content,
    )
    db.add(comment)
    db.flush()

    # 1. Tìm các thành viên được @mention
    mentioned_ids = _extract_mentioned_member_ids(db, project_id, comment_in.content, exclude_user_id=member.user_id)
    for uid in mentioned_ids:
        db.add(Notification(
            user_id=uid,
            type="comment_added",
            title=f"Bạn được nhắc tới trong bình luận: {task.title}",
            message=f"{member.user.full_name} đã nhắc tới bạn: {comment_in.content[:100]}",
            entity_type="comment",
            entity_id=comment.id,
            project_id=project_id,
        ))

    # 2. Thông báo cho người được giao việc và người tạo task (trừ người bình luận và người đã nhận thông báo mention)
    recipient_ids = {ta.user_id for ta in task.assignees if ta.user_id != member.user_id}
    if task.created_by != member.user_id:
        recipient_ids.add(task.created_by)
    recipient_ids -= mentioned_ids

    for uid in recipient_ids:
        db.add(Notification(
            user_id=uid,
            type="comment_added",
            title=f"Bình luận mới: {task.title}",
            message=f"{member.user.full_name} đã bình luận: {comment_in.content[:100]}",
            entity_type="comment",
            entity_id=comment.id,
            project_id=project_id,
        ))

    log = ActivityLog(
        project_id=project_id,
        task_id=task_id,
        user_id=member.user_id,
        entity_type="comment",
        entity_id=comment.id,
        action="created",
        new_value=json.dumps({"content": comment_in.content[:200]}, ensure_ascii=False),
    )
    db.add(log)
    db.commit()
    db.refresh(comment)

    resp = CommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        user_email=member.user.email,
        user_full_name=member.user.full_name,
        user_avatar_url=member.user.avatar_url,
    )

    notify_project_sync(project_id, "comment_added", resp.model_dump(mode="json"))
    for uid in (mentioned_ids | recipient_ids):
        notify_user_sync(uid, "notification_created", {"type": "comment_added", "task_id": task_id, "comment_id": comment.id})

    return resp


@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    project_id: int,
    task_id: int,
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Cập nhật bình luận (tác giả hoặc owner/manager)"""
    task, member = data

    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.task_id == task_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bình luận không tồn tại")

    if comment.user_id != member.user_id and member.role not in ["owner", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền sửa bình luận này")

    old_mentions = _extract_mentioned_member_ids(db, project_id, comment.content, exclude_user_id=member.user_id)
    new_mentions = _extract_mentioned_member_ids(db, project_id, comment_update.content, exclude_user_id=member.user_id)
    added_mentions = new_mentions - old_mentions

    comment.content = comment_update.content
    for uid in added_mentions:
        db.add(Notification(
            user_id=uid,
            type="comment_updated",
            title=f"Bạn được nhắc tới trong bình luận: {task.title}",
            message=f"{member.user.full_name} đã nhắc tới bạn: {comment_update.content[:100]}",
            entity_type="comment",
            entity_id=comment.id,
            project_id=project_id,
        ))

    db.commit()
    db.refresh(comment)

    resp = CommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        user_id=comment.user_id,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        user_email=comment.user.email if comment.user else None,
        user_full_name=comment.user.full_name if comment.user else None,
        user_avatar_url=comment.user.avatar_url if comment.user else None,
    )
    notify_project_sync(project_id, "comment_updated", resp.model_dump(mode="json"))
    for uid in added_mentions:
        notify_user_sync(uid, "notification_created", {"type": "comment_updated", "task_id": task_id, "comment_id": comment.id})
    return resp


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    project_id: int,
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Xoá bình luận (tác giả tự xoá, hoặc owner/manager xoá được của người khác)"""
    task, member = data

    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.task_id == task_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bình luận không tồn tại")

    if comment.user_id != member.user_id and member.role not in ["owner", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xoá bình luận này")

    db.delete(comment)
    db.commit()

    notify_project_sync(project_id, "comment_deleted", {"task_id": task_id, "comment_id": comment_id})
    return None
