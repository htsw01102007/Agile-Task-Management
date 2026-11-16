from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import os

from app.db.session import get_db
from app.core.permissions import (
    get_project_and_membership,
    require_project_roles,
    get_task_and_membership,
    get_task_with_write_check,
    get_task_for_delete,
    get_task_for_restore,
    validate_assignees_not_viewers,
)
from app.core.deps import get_current_user
from app.core.ws_manager import notify_project_sync, notify_user_sync
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task, TaskAssignee, TaskLabel
from app.models.list import ListModel
from app.models.label import Label
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskMove,
    TaskReorder,
    TaskAssigneeAssignRequest,
    TaskLabelAttachRequest,
    TaskResponse,
    TaskDetailResponse,
    TaskAssigneeResponse,
    TaskLabelResponse,
)
from app.schemas.checklist import ChecklistItemResponse

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])
my_tasks_router = APIRouter(prefix="/tasks", tags=["My Tasks"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_next_position(db: Session, list_id: int) -> int:
    """Get next position for new task in list"""
    max_pos = (
        db.query(Task.position)
        .filter(Task.list_id == list_id, Task.is_deleted.is_(False))
        .order_by(Task.position.desc())
        .first()
    )
    return (max_pos[0] + 1) if max_pos else 0


def _renumber_list_tasks(db: Session, list_id: int, exclude_task_id: Optional[int] = None) -> None:
    """Renumber positions in a list to be sequential (0, 1, 2, ...) without committing prematurely"""
    query = db.query(Task).filter(Task.list_id == list_id, Task.is_deleted.is_(False))
    if exclude_task_id is not None:
        query = query.filter(Task.id != exclude_task_id)
    tasks = query.order_by(Task.position.asc(), Task.id.asc()).all()
    for idx, t in enumerate(tasks):
        t.position = idx


def _create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    message: str,
    entity_type: str,
    entity_id: int,
    project_id: int,
) -> Notification:
    """Helper to create notification"""
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        project_id=project_id,
    )
    db.add(notif)
    return notif


def _create_activity_log(
    db: Session,
    project_id: int,
    task_id: Optional[int],
    user_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
) -> ActivityLog:
    """Helper to create activity log"""
    log = ActivityLog(
        project_id=project_id,
        task_id=task_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(log)
    return log


def _build_task_detail_response(db: Session, task: Task) -> TaskDetailResponse:
    """Build detailed task response with relationships and checklist progress %"""
    assignees = []
    for ta in task.assignees:
        assignees.append(TaskAssigneeResponse(
            user_id=ta.user_id,
            assigned_at=ta.assigned_at,
            user_email=ta.user.email if ta.user else None,
            user_full_name=ta.user.full_name if ta.user else None,
            user_avatar_url=ta.user.avatar_url if ta.user else None,
        ))

    labels = []
    for tl in task.labels:
        if tl.label:
            labels.append(TaskLabelResponse(
                label_id=tl.label_id,
                label_name=tl.label.name,
                label_color=tl.label.color,
            ))

    sorted_checklist = sorted(task.checklist_items, key=lambda c: (c.position, c.id))
    checklist = [
        ChecklistItemResponse.model_validate(ci) for ci in sorted_checklist
    ]
    checklist_total = len(checklist)
    checklist_completed = sum(1 for ci in checklist if ci.is_done)
    checklist_progress = (
        round((checklist_completed / checklist_total) * 100, 2)
        if checklist_total > 0
        else 0.0
    )

    return TaskDetailResponse(
        id=task.id,
        project_id=task.project_id,
        list_id=task.list_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        position=task.position,
        start_date=task.start_date,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_by=task.created_by,
        is_deleted=task.is_deleted,
        deleted_at=task.deleted_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignees=assignees,
        labels=labels,
        checklist_items=checklist,
        checklist_total=checklist_total,
        checklist_completed=checklist_completed,
        checklist_progress=checklist_progress,
        comments_count=len(task.comments),
        attachments_count=len(task.attachments),
        creator_name=task.creator.full_name if task.creator else None,
    )


def _query_my_tasks(
    db: Session,
    current_user_id: int,
    response: Response,
    project_id: Optional[int] = None,
    list_id: Optional[int] = None,
    priority: Optional[str] = None,
    is_completed: Optional[bool] = None,
    is_overdue: Optional[bool] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    label_ids: Optional[str] = None,
    sort_by: str = "due_date",
    order: str = "asc",
    page: int = 1,
    size: int = 20,
) -> List[Task]:
    query = (
        db.query(Task)
        .join(TaskAssignee, TaskAssignee.task_id == Task.id)
        .join(Project, Project.id == Task.project_id)
        .join(
            ProjectMember,
            (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == current_user_id),
        )
        .filter(
            TaskAssignee.user_id == current_user_id,
            Task.is_deleted.is_(False),
            Project.deleted_at.is_(None),
        )
    )

    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if list_id is not None:
        query = query.filter(Task.list_id == list_id)
    if priority:
        query = query.filter(Task.priority == priority)
    if is_completed is not None:
        if is_completed:
            query = query.filter(Task.completed_at.isnot(None))
        else:
            query = query.filter(Task.completed_at.is_(None))
    if is_overdue is not None:
        now = datetime.now(timezone.utc)
        if is_overdue:
            query = query.filter(Task.due_date.isnot(None), Task.due_date < now, Task.completed_at.is_(None))
        else:
            query = query.filter((Task.due_date.is_(None)) | (Task.due_date >= now) | (Task.completed_at.isnot(None)))
    if due_date_from:
        query = query.filter(Task.due_date >= due_date_from)
    if due_date_to:
        query = query.filter(Task.due_date <= due_date_to)
    if search:
        keyword = f"%{search}%"
        query = query.filter(Task.title.ilike(keyword) | Task.description.ilike(keyword))
    if label_ids:
        label_id_list = [int(x) for x in label_ids.split(",") if x.strip().isdigit()]
        if label_id_list:
            query = query.join(TaskLabel, TaskLabel.task_id == Task.id).filter(TaskLabel.label_id.in_(label_id_list))

    query = query.distinct()

    sort_col = {
        "due_date": Task.due_date,
        "priority": Task.priority,
        "created_at": Task.created_at,
        "position": Task.position,
    }.get(sort_by, Task.due_date)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc(), Task.id.asc())

    total = query.count()
    tasks = query.offset((page - 1) * size).limit(size).all()

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Size"] = str(size)
    response.headers["X-Total-Pages"] = str((total + size - 1) // size)
    return tasks


# ===== GLOBAL /api/tasks/my-tasks (Across all projects or filtered by project_id) =====

@my_tasks_router.get("/my-tasks", response_model=List[TaskResponse])
def get_all_my_tasks(
    response: Response,
    project_id: Optional[int] = Query(None, description="Lọc theo dự án cụ thể (tùy chọn)"),
    list_id: Optional[int] = Query(None, description="Lọc theo cột (list)"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|urgent)$"),
    is_completed: Optional[bool] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    due_date_from: Optional[datetime] = Query(None),
    due_date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    label_ids: Optional[str] = Query(None),
    sort_by: str = Query("due_date", pattern="^(due_date|priority|created_at|position)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xem công việc của tôi được giao ở mọi dự án (hoặc dự án cụ thể), sắp theo hạn chót"""
    return _query_my_tasks(
        db=db,
        current_user_id=current_user.id,
        response=response,
        project_id=project_id,
        list_id=list_id,
        priority=priority,
        is_completed=is_completed,
        is_overdue=is_overdue,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        search=search,
        label_ids=label_ids,
        sort_by=sort_by,
        order=order,
        page=page,
        size=size,
    )


# ===== CORE PROJECT TASK CRUD & SEARCH/FILTER/PAGINATION =====

@router.get("", response_model=List[TaskResponse])
def list_tasks(
    project_id: int,
    response: Response,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_project_and_membership),
    list_id: Optional[int] = Query(None, description="Lọc theo list"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|urgent)$"),
    assignee_id: Optional[int] = Query(None, description="Lọc theo người được giao"),
    label_ids: Optional[str] = Query(None, description="Lọc theo label (comma-separated)"),
    due_date_from: Optional[datetime] = Query(None),
    due_date_to: Optional[datetime] = Query(None),
    is_completed: Optional[bool] = Query(None),
    is_overdue: Optional[bool] = Query(None, description="Lọc công việc quá hạn"),
    search: Optional[str] = Query(None, description="Tìm theo tiêu đề/mô tả"),
    sort_by: str = Query("position", pattern="^(position|due_date|priority|created_at)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Danh sách task trong dự án với filter, search, sort và pagination"""
    project, member = data

    query = db.query(Task).filter(Task.project_id == project_id, Task.is_deleted.is_(False))

    if list_id:
        query = query.filter(Task.list_id == list_id)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.join(TaskAssignee, TaskAssignee.task_id == Task.id).filter(TaskAssignee.user_id == assignee_id)
    if label_ids:
        label_id_list = [int(x) for x in label_ids.split(",") if x.strip().isdigit()]
        if label_id_list:
            query = query.join(TaskLabel, TaskLabel.task_id == Task.id).filter(TaskLabel.label_id.in_(label_id_list))
    if due_date_from:
        query = query.filter(Task.due_date >= due_date_from)
    if due_date_to:
        query = query.filter(Task.due_date <= due_date_to)
    if is_completed is not None:
        if is_completed:
            query = query.filter(Task.completed_at.isnot(None))
        else:
            query = query.filter(Task.completed_at.is_(None))
    if is_overdue is not None:
        now = datetime.now(timezone.utc)
        if is_overdue:
            query = query.filter(Task.due_date.isnot(None), Task.due_date < now, Task.completed_at.is_(None))
        else:
            query = query.filter((Task.due_date.is_(None)) | (Task.due_date >= now) | (Task.completed_at.isnot(None)))
    if search:
        keyword = f"%{search}%"
        query = query.filter(Task.title.ilike(keyword) | Task.description.ilike(keyword))

    query = query.distinct()

    sort_col = {
        "position": Task.position,
        "due_date": Task.due_date,
        "priority": Task.priority,
        "created_at": Task.created_at,
    }.get(sort_by, Task.position)
    query = query.order_by(sort_col.desc() if order == "desc" else sort_col.asc(), Task.id.asc())

    total = query.count()
    tasks = query.offset((page - 1) * size).limit(size).all()

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Size"] = str(size)
    response.headers["X-Total-Pages"] = str((total + size - 1) // size)

    return tasks


@router.get("/my-tasks", response_model=List[TaskResponse])
def get_my_tasks_in_project(
    project_id: int,
    response: Response,
    list_id: Optional[int] = Query(None),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|urgent)$"),
    is_completed: Optional[bool] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    due_date_from: Optional[datetime] = Query(None),
    due_date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    label_ids: Optional[str] = Query(None),
    sort_by: str = Query("due_date", pattern="^(due_date|priority|created_at|position)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    data: tuple = Depends(get_project_and_membership),
):
    """Công việc được giao cho user hiện tại trong dự án này"""
    project, member = data
    return _query_my_tasks(
        db=db,
        current_user_id=member.user_id,
        response=response,
        project_id=project_id,
        list_id=list_id,
        priority=priority,
        is_completed=is_completed,
        is_overdue=is_overdue,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        search=search,
        label_ids=label_ids,
        sort_by=sort_by,
        order=order,
        page=page,
        size=size,
    )


@router.get("/deleted", response_model=List[TaskResponse])
def list_deleted_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(require_project_roles("owner", "manager", allow_read_only_when_inactive=True)),
):
    """Danh sách các công việc đã xoá mềm trong dự án (Thùng rác)"""
    project, _ = data
    return (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.is_deleted.is_(True))
        .order_by(Task.deleted_at.desc(), Task.id.desc())
        .all()
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task_detail(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_and_membership),
):
    """Chi tiết task kèm assignees, labels, checklist (với % hoàn thành), comments count"""
    task, member = data
    return _build_task_detail_response(db, task)


@router.post("", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    data: tuple = Depends(require_project_roles("owner", "manager", "member")),
):
    """Tạo task mới"""
    project, member = data

    list_obj = db.query(ListModel).filter(ListModel.id == task_in.list_id, ListModel.project_id == project_id).first()
    if not list_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Danh sách không tồn tại")

    if task_in.start_date and task_in.due_date and task_in.due_date < task_in.start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hạn chót không được sớm hơn ngày bắt đầu")

    position = task_in.position if task_in.position is not None else _get_next_position(db, task_in.list_id)
    completed_at = datetime.now(timezone.utc) if list_obj.is_done_column else None

    task = Task(
        project_id=project_id,
        list_id=task_in.list_id,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority,
        position=position,
        start_date=task_in.start_date,
        due_date=task_in.due_date,
        completed_at=completed_at,
        created_by=member.user_id,
    )
    db.add(task)
    db.flush()

    notified_users = []
    if task_in.assignee_ids:
        valid_ids = validate_assignees_not_viewers(db, project_id, list(dict.fromkeys(task_in.assignee_ids)))
        for uid in valid_ids:
            db.add(TaskAssignee(task_id=task.id, user_id=uid))
            if uid != member.user_id:
                _create_notification(
                    db,
                    uid,
                    "task_assigned",
                    f"Bạn được giao việc: {task.title}",
                    f'Bạn được giao việc "{task.title}" trong dự án "{project.name}"',
                    "task",
                    task.id,
                    project_id,
                )
                notified_users.append(uid)

    if task_in.label_ids:
        for lid in dict.fromkeys(task_in.label_ids):
            label = db.query(Label).filter(Label.id == lid, Label.project_id == project_id).first()
            if label:
                db.add(TaskLabel(task_id=task.id, label_id=lid))

    _create_activity_log(
        db,
        project_id,
        task.id,
        member.user_id,
        "task",
        task.id,
        "created",
        None,
        f'{{"title": "{task.title}", "priority": "{task.priority}"}}',
    )

    db.commit()
    db.refresh(task)

    detail = _build_task_detail_response(db, task)
    notify_project_sync(project_id, "task_created", detail.model_dump(mode="json"))
    for uid in notified_users:
        notify_user_sync(uid, "notification_created", {"type": "task_assigned", "task_id": task.id, "project_id": project_id})

    return detail


@router.put("/{task_id}", response_model=TaskDetailResponse)
def update_task(
    project_id: int,
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Cập nhật task"""
    task, member = data

    update_data = task_update.model_dump(exclude_unset=True)

    new_start = update_data.get("start_date", task.start_date)
    new_due = update_data.get("due_date", task.due_date)
    if new_start and new_due and new_due < new_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hạn chót không được sớm hơn ngày bắt đầu")

    old_list_id = task.list_id
    old_position = task.position
    target_list_id = update_data.get("list_id", old_list_id)

    changes = {}
    for field, value in update_data.items():
        if field in ("list_id", "position"):
            continue
        old_value = getattr(task, field)
        if old_value != value:
            changes[field] = {"old": str(old_value) if old_value else None, "new": str(value) if value else None}
            setattr(task, field, value)

    if "list_id" in update_data and target_list_id != old_list_id:
        new_list = db.query(ListModel).filter(ListModel.id == target_list_id, ListModel.project_id == project_id).first()
        if not new_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Danh sách đích không tồn tại")

        task.list_id = new_list.id
        task.position = (
            update_data["position"]
            if update_data.get("position") is not None
            else _get_next_position(db, new_list.id)
        )

        if new_list.is_done_column:
            task.completed_at = datetime.now(timezone.utc)
        elif task.completed_at:
            task.completed_at = None

        _renumber_list_tasks(db, old_list_id, exclude_task_id=task.id)
        _renumber_list_tasks(db, new_list.id)

        _create_activity_log(
            db,
            project_id,
            task.id,
            member.user_id,
            "task",
            task.id,
            "moved",
            f'{{"list_id": {old_list_id}, "position": {old_position}}}',
            f'{{"list_id": {new_list.id}, "position": {task.position}}}',
        )
    elif "position" in update_data and update_data["position"] is not None:
        task.position = update_data["position"]
        _renumber_list_tasks(db, task.list_id)

    if changes:
        _create_activity_log(
            db,
            project_id,
            task.id,
            member.user_id,
            "task",
            task.id,
            "updated",
            str({k: v["old"] for k, v in changes.items()}),
            str({k: v["new"] for k, v in changes.items()}),
        )

    db.commit()
    db.refresh(task)

    detail = _build_task_detail_response(db, task)
    notify_project_sync(project_id, "task_updated", detail.model_dump(mode="json"))
    return detail


@router.patch("/{task_id}/move", response_model=TaskDetailResponse)
def move_task(
    project_id: int,
    task_id: int,
    move_data: TaskMove,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Di chuyển task sang list khác (hoặc trong cùng list) với vị trí cụ thể trong một transaction"""
    task, member = data

    new_list = db.query(ListModel).filter(ListModel.id == move_data.list_id, ListModel.project_id == project_id).first()
    if not new_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Danh sách đích không tồn tại")

    if new_list.id == task.list_id and move_data.position == task.position:
        return _build_task_detail_response(db, task)

    old_list_id = task.list_id
    old_position = task.position

    if old_list_id == move_data.list_id:
        # Di chuyển trong cùng 1 list
        siblings = (
            db.query(Task)
            .filter(Task.list_id == old_list_id, Task.is_deleted.is_(False), Task.id != task.id)
            .order_by(Task.position.asc(), Task.id.asc())
            .all()
        )
        target_pos = max(0, min(move_data.position, len(siblings)))
        siblings.insert(target_pos, task)
        for idx, t in enumerate(siblings):
            t.position = idx
    else:
        # Di chuyển sang list khác
        _renumber_list_tasks(db, old_list_id, exclude_task_id=task.id)
        dest_tasks = (
            db.query(Task)
            .filter(Task.list_id == move_data.list_id, Task.is_deleted.is_(False), Task.id != task.id)
            .order_by(Task.position.asc(), Task.id.asc())
            .all()
        )
        target_pos = max(0, min(move_data.position, len(dest_tasks)))
        task.list_id = move_data.list_id
        dest_tasks.insert(target_pos, task)
        for idx, t in enumerate(dest_tasks):
            t.position = idx

        if new_list.is_done_column:
            task.completed_at = datetime.now(timezone.utc)
        elif task.completed_at:
            task.completed_at = None

    _create_activity_log(
        db,
        project_id,
        task.id,
        member.user_id,
        "task",
        task.id,
        "moved",
        f'{{"list_id": {old_list_id}, "position": {old_position}}}',
        f'{{"list_id": {move_data.list_id}, "position": {task.position}}}',
    )

    db.commit()
    db.refresh(task)

    detail = _build_task_detail_response(db, task)
    notify_project_sync(project_id, "task_moved", detail.model_dump(mode="json"))
    return detail


@router.patch("/reorder", response_model=List[TaskResponse])
def reorder_tasks(
    project_id: int,
    reorder: TaskReorder,
    db: Session = Depends(get_db),
    data: tuple = Depends(require_project_roles("owner", "manager", "member")),
):
    """Sắp xếp lại thứ tự nhiều task trong cùng list"""
    project, member = data

    if not reorder.task_ids:
        return []

    tasks = (
        db.query(Task)
        .filter(Task.id.in_(reorder.task_ids), Task.project_id == project_id, Task.is_deleted.is_(False))
        .all()
    )
    if len(tasks) != len(set(reorder.task_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Một hoặc nhiều task không hợp lệ")

    list_ids = set(t.list_id for t in tasks)
    if len(list_ids) > 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chỉ có thể sắp xếp task trong cùng một danh sách")

    task_map = {t.id: t for t in tasks}
    ordered_tasks = []
    for idx, tid in enumerate(reorder.task_ids):
        t = task_map[tid]
        t.position = idx
        ordered_tasks.append(t)

    db.commit()
    notify_project_sync(
        project_id,
        "task_reordered",
        {"list_id": next(iter(list_ids)), "task_ids": reorder.task_ids},
    )
    return ordered_tasks


# ===== TASK ASSIGNEES ENDPOINTS =====

@router.get("/{task_id}/assignees", response_model=List[TaskAssigneeResponse])
def list_task_assignees(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_and_membership),
):
    """Danh sách người thực hiện của task"""
    task, _ = data
    return [
        TaskAssigneeResponse(
            user_id=ta.user_id,
            assigned_at=ta.assigned_at,
            user_email=ta.user.email if ta.user else None,
            user_full_name=ta.user.full_name if ta.user else None,
            user_avatar_url=ta.user.avatar_url if ta.user else None,
        )
        for ta in task.assignees
    ]


@router.post("/{task_id}/assignees", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
def assign_task_members(
    project_id: int,
    task_id: int,
    assign_in: TaskAssigneeAssignRequest,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Giao việc cho thành viên trong dự án (chỉ cho phép thành viên thuộc dự án và không phải viewer)"""
    task, member = data

    target_ids: List[int] = []
    if assign_in.user_id is not None:
        target_ids.append(assign_in.user_id)
    if assign_in.user_ids:
        target_ids.extend(assign_in.user_ids)
    target_ids = list(dict.fromkeys(target_ids))

    if not target_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng truyền user_id hoặc user_ids để giao việc",
        )

    valid_ids = validate_assignees_not_viewers(db, project_id, target_ids)
    existing_ids = {ta.user_id for ta in task.assignees}
    project = db.query(Project).filter(Project.id == project_id).first()

    newly_assigned = []
    for uid in valid_ids:
        if uid not in existing_ids:
            db.add(TaskAssignee(task_id=task.id, user_id=uid))
            newly_assigned.append(uid)
            if uid != member.user_id:
                _create_notification(
                    db,
                    uid,
                    "task_assigned",
                    f"Bạn được giao việc: {task.title}",
                    f'Bạn được giao việc "{task.title}" trong dự án "{project.name if project else project_id}"',
                    "task",
                    task.id,
                    project_id,
                )

    if newly_assigned:
        _create_activity_log(
            db,
            project_id,
            task.id,
            member.user_id,
            "assignee",
            task.id,
            "assigned",
            None,
            f'{{"user_ids": {newly_assigned}}}',
        )

    db.commit()
    db.refresh(task)

    detail = _build_task_detail_response(db, task)
    notify_project_sync(project_id, "task_updated", detail.model_dump(mode="json"))
    for uid in newly_assigned:
        if uid != member.user_id:
            notify_user_sync(uid, "notification_created", {"type": "task_assigned", "task_id": task.id, "project_id": project_id})

    return detail


@router.delete("/{task_id}/assignees/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_task_member(
    project_id: int,
    task_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Bỏ giao việc một thành viên khỏi task"""
    task, member = data

    ta = (
        db.query(TaskAssignee)
        .filter(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id)
        .first()
    )
    if not ta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng chưa được giao công việc này",
        )

    db.delete(ta)
    _create_activity_log(
        db,
        project_id,
        task.id,
        member.user_id,
        "assignee",
        task.id,
        "unassigned",
        f'{{"user_id": {user_id}}}',
        None,
    )
    db.commit()

    notify_project_sync(project_id, "task_updated", {"task_id": task.id, "unassigned_user_id": user_id})
    return None


# ===== TASK LABELS ENDPOINTS =====

@router.post("/{task_id}/labels", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
def attach_labels_to_task(
    project_id: int,
    task_id: int,
    label_in: TaskLabelAttachRequest,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Gắn một hoặc nhiều nhãn của dự án vào task"""
    task, member = data

    target_label_ids: List[int] = []
    if label_in.label_id is not None:
        target_label_ids.append(label_in.label_id)
    if label_in.label_ids:
        target_label_ids.extend(label_in.label_ids)
    target_label_ids = list(dict.fromkeys(target_label_ids))

    if not target_label_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng truyền label_id hoặc label_ids",
        )

    existing_lids = {tl.label_id for tl in task.labels}
    for lid in target_label_ids:
        label = db.query(Label).filter(Label.id == lid, Label.project_id == project_id).first()
        if not label:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nhãn ID {lid} không tồn tại trong dự án",
            )
        if lid not in existing_lids:
            db.add(TaskLabel(task_id=task.id, label_id=lid))

    db.commit()
    db.refresh(task)
    detail = _build_task_detail_response(db, task)
    notify_project_sync(project_id, "task_updated", detail.model_dump(mode="json"))
    return detail


@router.delete("/{task_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_label_from_task(
    project_id: int,
    task_id: int,
    label_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_with_write_check),
):
    """Gỡ nhãn khỏi task"""
    task, _ = data
    tl = (
        db.query(TaskLabel)
        .filter(TaskLabel.task_id == task_id, TaskLabel.label_id == label_id)
        .first()
    )
    if not tl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nhãn chưa được gắn vào công việc này",
        )
    db.delete(tl)
    db.commit()
    notify_project_sync(project_id, "task_updated", {"task_id": task.id, "detached_label_id": label_id})
    return None


# ===== SOFT DELETE & RESTORE =====

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_for_delete),
):
    """Xoá mềm task (member chỉ xoá task do mình tạo, manager/owner xoá được mọi task)"""
    task, member = data

    old_list_id = task.list_id
    task.is_deleted = True
    task.deleted_at = datetime.now(timezone.utc)
    _renumber_list_tasks(db, old_list_id, exclude_task_id=task.id)
    _create_activity_log(
        db,
        project_id,
        task.id,
        member.user_id,
        "task",
        task.id,
        "deleted",
        f'{{"title": "{task.title}"}}',
        None,
    )
    db.commit()

    notify_project_sync(project_id, "task_deleted", {"task_id": task_id, "list_id": old_list_id})
    return None


@router.post("/{task_id}/restore", response_model=TaskDetailResponse)
def restore_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_task_for_restore),
):
    """Khôi phục task đã xoá mềm (trong 30 ngày) - chỉ owner/manager"""
    task, member = data

    if task.deleted_at:
        deleted_dt = task.deleted_at
        if deleted_dt.tzinfo is None:
            deleted_dt = deleted_dt.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - deleted_dt).days > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể khôi phục task đã xoá quá 30 ngày",
            )

    task.is_deleted = False
    task.deleted_at = None
    task.position = _get_next_position(db, task.list_id)
    _create_activity_log(
        db,
        project_id,
        task.id,
        member.user_id,
        "task",
        task.id,
        "restored",
        None,
        f'{{"title": "{task.title}"}}',
    )
    db.commit()
    db.refresh(task)

    detail = _build_task_detail_response(db, task)
    notify_project_sync(project_id, "task_restored", detail.model_dump(mode="json"))
    return detail
