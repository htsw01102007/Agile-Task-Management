from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.crud import auth as auth_crud
from app.db.session import get_db
from app.models.list import ListModel
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.auth import RegisterRequest

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str
    avatar_url: Optional[str] = None
    system_role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class AdminOverviewSummary(BaseModel):
    user_count: int = 0
    active_user_count: int = 0
    project_count: int = 0
    active_project_count: int = 0
    task_count: int = 0
    completed_task_count: int = 0
    recent_users: List[AdminUserOut] = []


class AdminUpdateUserRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(..., min_length=1, max_length=150)


class AdminToggleStatusRequest(BaseModel):
    is_active: bool


@router.get("/summary", response_model=AdminOverviewSummary)
def get_admin_summary(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
):
    """Số liệu tổng hợp toàn hệ thống dành cho Admin trên Dashboard"""
    user_count = db.query(User).count()
    active_user_count = db.query(User).filter(User.is_active.is_(True)).count()

    active_projects_q = db.query(Project).filter(Project.deleted_at.is_(None))
    project_count = active_projects_q.count()
    active_project_count = active_projects_q.filter(Project.status == "active").count()

    tasks_q = (
        db.query(Task, ListModel.is_done_column)
        .join(Project, Project.id == Task.project_id)
        .join(ListModel, ListModel.id == Task.list_id)
        .filter(Task.is_deleted.is_(False), Project.deleted_at.is_(None))
        .all()
    )
    task_count = len(tasks_q)
    completed_task_count = sum(
        1 for t, is_done_col in tasks_q if t.completed_at is not None or bool(is_done_col)
    )

    recent_users = (
        db.query(User)
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(5)
        .all()
    )

    return AdminOverviewSummary(
        user_count=user_count,
        active_user_count=active_user_count,
        project_count=project_count,
        active_project_count=active_project_count,
        task_count=task_count,
        completed_task_count=completed_task_count,
        recent_users=[AdminUserOut.model_validate(u) for u in recent_users],
    )


@router.get("", response_model=List[AdminUserOut])
def list_users_admin(
    response: Response,
    q: Optional[str] = Query(None, description="Tìm kiếm theo tên, email hoặc username"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái hoạt động"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
):
    """Danh sách tài khoản người dùng (hỗ trợ tìm kiếm, lọc và phân trang)"""
    query = db.query(User)
    if q:
        keyword = f"%{q.strip().lower()}%"
        query = query.filter(
            (func.lower(User.full_name).like(keyword))
            | (func.lower(User.email).like(keyword))
            | (func.lower(User.username).like(keyword))
        )
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    users = (
        query.order_by(User.created_at.desc(), User.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    response.headers["X-Total-Count"] = str(total)
    return users


@router.post("", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
):
    """Admin tạo tài khoản thành viên mới"""
    created = auth_crud.register_user(db, body)
    user = db.query(User).filter(User.id == created.id).first()
    return user


@router.put("/{user_id}", response_model=AdminUserOut)
def update_user_admin(
    user_id: int,
    body: AdminUpdateUserRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
):
    """Admin cập nhật họ tên tài khoản"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")

    user.full_name = body.full_name
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=AdminUserOut)
def toggle_user_status_admin(
    user_id: int,
    body: AdminToggleStatusRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
):
    """Admin khóa hoặc mở khóa tài khoản thành viên"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")

    if user.system_role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể khóa tài khoản quản trị viên",
        )

    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return user

