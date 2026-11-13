from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.ws_manager import notify_user_sync
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task, TaskAssignee
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationMarkRead,
    NotificationUnreadCount,
    NotificationBellResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def scan_and_create_deadline_notifications(
    db: Session,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> Tuple[List[Notification], int, int]:
    """
    Quét các task chưa hoàn thành có hạn chót:
    - Còn <= 24 giờ tới hạn chót -> Tạo thông báo 'task_due_soon'
    - Đã quá hạn chót -> Tạo thông báo 'task_overdue'
    Đảm bảo không tạo trùng thông báo cùng loại cho cùng (user_id, task_id).
    """
    now_utc = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)
    soon_threshold = now_naive + timedelta(hours=24)

    query = (
        db.query(Task, TaskAssignee.user_id, Project.name)
        .join(TaskAssignee, TaskAssignee.task_id == Task.id)
        .join(Project, Project.id == Task.project_id)
        .filter(
            Task.is_deleted.is_(False),
            Task.completed_at.is_(None),
            Task.due_date.isnot(None),
            Task.due_date <= soon_threshold,
            Project.deleted_at.is_(None),
        )
    )
    if user_id is not None:
        query = query.filter(TaskAssignee.user_id == user_id)
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)

    rows = query.all()
    if not rows:
        return [], 0, 0

    created_notifications: List[Notification] = []
    due_soon_count = 0
    overdue_count = 0

    for task, assignee_uid, project_name in rows:
        due_dt = task.due_date
        if due_dt.tzinfo is not None:
            due_dt = due_dt.astimezone(timezone.utc).replace(tzinfo=None)

        if due_dt < now_naive:
            notif_type = "task_overdue"
            title = f"Công việc quá hạn: {task.title}"
            message = f'Công việc "{task.title}" trong dự án "{project_name}" đã quá hạn vào {due_dt.strftime("%Y-%m-%d %H:%M")}.'
        else:
            notif_type = "task_due_soon"
            title = f"Sắp đến hạn (trong 24h): {task.title}"
            message = f'Công việc "{task.title}" trong dự án "{project_name}" sẽ đến hạn vào {due_dt.strftime("%Y-%m-%d %H:%M")}.'

        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == assignee_uid,
                Notification.type == notif_type,
                Notification.entity_type == "task",
                Notification.entity_id == task.id,
            )
            .first()
        )
        if not existing:
            notif = Notification(
                user_id=assignee_uid,
                type=notif_type,
                title=title,
                message=message,
                entity_type="task",
                entity_id=task.id,
                project_id=task.project_id,
            )
            db.add(notif)
            created_notifications.append(notif)
            if notif_type == "task_due_soon":
                due_soon_count += 1
            else:
                overdue_count += 1

    if created_notifications:
        db.commit()
        for notif in created_notifications:
            db.refresh(notif)
            notify_user_sync(
                notif.user_id,
                "deadline_reminder",
                NotificationResponse.model_validate(notif).model_dump(mode="json"),
            )

    return created_notifications, due_soon_count, overdue_count


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    is_read: Optional[bool] = Query(None),
    project_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    auto_check_deadline: bool = Query(True, description="Tự động kiểm tra và tạo thông báo nhắc hạn trước khi trả về"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Danh sách thông báo của user hiện tại (kèm phân trang)"""
    if auto_check_deadline:
        scan_and_create_deadline_notifications(db, user_id=current_user.id, project_id=project_id)

    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    if project_id:
        query = query.filter(Notification.project_id == project_id)
    if type:
        query = query.filter(Notification.type == type)

    query = query.order_by(Notification.created_at.desc(), Notification.id.desc())
    total = query.count()
    notifications = query.offset((page - 1) * size).limit(size).all()

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Size"] = str(size)
    response.headers["X-Total-Pages"] = str((total + size - 1) // size)

    return notifications


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notif_in: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo thông báo mới cho người dùng (trong dự án hoặc cá nhân)"""
    if notif_in.project_id is not None:
        member = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == notif_in.project_id,
                ProjectMember.user_id == current_user.id,
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không phải thành viên của dự án này",
            )

    target_user = db.query(User).filter(User.id == notif_in.user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Người nhận không tồn tại")

    notif = Notification(
        user_id=notif_in.user_id,
        type=notif_in.type,
        title=notif_in.title,
        message=notif_in.message,
        entity_type=notif_in.entity_type,
        entity_id=notif_in.entity_id,
        project_id=notif_in.project_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)

    resp = NotificationResponse.model_validate(notif)
    notify_user_sync(notif.user_id, "notification_created", resp.model_dump(mode="json"))
    return notif


@router.get("/unread-count", response_model=NotificationUnreadCount)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Số lượng thông báo chưa đọc (tự động cập nhật nhắc hạn)"""
    scan_and_create_deadline_notifications(db, user_id=current_user.id)
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .count()
    )
    return NotificationUnreadCount(unread_count=count)


@router.get("/bell", response_model=NotificationBellResponse)
def get_notification_bell(
    limit: int = Query(10, ge=1, le=50),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    API Chuông thông báo & nhắc hạn:
    - Tự động quét công việc sắp đến hạn (trong 24h) và quá hạn của người dùng.
    - Trả về tổng số thông báo chưa đọc và danh sách thông báo mới nhất.
    """
    _, due_soon_created, overdue_created = scan_and_create_deadline_notifications(
        db, user_id=current_user.id, project_id=project_id
    )
    unread_query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    )
    items_query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if project_id is not None:
        unread_query = unread_query.filter(Notification.project_id == project_id)
        items_query = items_query.filter(Notification.project_id == project_id)

    unread_count = unread_query.count()
    items = (
        items_query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .all()
    )
    return NotificationBellResponse(
        unread_count=unread_count,
        due_soon_created=due_soon_created,
        overdue_created=overdue_created,
        items=[NotificationResponse.model_validate(n) for n in items],
    )


@router.post("/check-deadlines", response_model=List[NotificationResponse])
def check_deadlines(
    project_id: Optional[int] = Query(None, description="Quét theo dự án cụ thể (hoặc cá nhân nếu bỏ trống)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chủ động quét và tạo thông báo nhắc hạn (task_due_soon <= 24h & task_overdue)"""
    if project_id is not None:
        member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không phải thành viên của dự án này",
            )
        # Owner/Manager có thể quét cho toàn bộ thành viên trong dự án
        target_uid = None if member.role in ("owner", "manager") else current_user.id
        created, _, _ = scan_and_create_deadline_notifications(db, user_id=target_uid, project_id=project_id)
    else:
        created, _, _ = scan_and_create_deadline_notifications(db, user_id=current_user.id)

    return created


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_as_read(
    mark_in: Optional[NotificationMarkRead] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_id: Optional[int] = Query(None),
):
    """Đánh dấu tất cả thông báo đã đọc (hoặc theo danh sách notification_ids / project)"""
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    )
    if project_id:
        query = query.filter(Notification.project_id == project_id)
    if mark_in and mark_in.notification_ids:
        query = query.filter(Notification.id.in_(mark_in.notification_ids))
    query.update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return None


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đánh dấu một thông báo đã đọc"""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thông báo không tồn tại")

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return notification
