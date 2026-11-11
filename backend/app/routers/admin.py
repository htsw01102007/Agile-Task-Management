from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.security import hash_password
from app.db.session import get_db
from app.models.list import ListModel
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.admin import (
    AdminDashboardResponse,
    AdminUserCreate,
    AdminUserResponse,
    AdminUserStatusUpdate,
    AdminUserUpdate,
)

router = APIRouter(prefix="/admin/users", tags=["System Admin"])


@router.get("/summary", response_model=AdminDashboardResponse)
def get_admin_dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    active_project_filter = Project.deleted_at.is_(None)
    active_task_filter = Task.deleted_at.is_(None), Project.deleted_at.is_(None)
    return AdminDashboardResponse(
        user_count=db.query(func.count(User.id)).scalar() or 0,
        active_user_count=db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0,
        project_count=db.query(func.count(Project.id)).filter(active_project_filter).scalar() or 0,
        active_project_count=db.query(func.count(Project.id)).filter(
            active_project_filter, Project.status == "active"
        ).scalar() or 0,
        task_count=db.query(func.count(Task.id))
        .join(Project, Project.id == Task.project_id)
        .filter(*active_task_filter)
        .scalar() or 0,
        completed_task_count=db.query(func.count(Task.id))
        .join(Project, Project.id == Task.project_id)
        .join(ListModel, ListModel.id == Task.list_id)
        .filter(*active_task_filter, ListModel.is_done_column.is_(True))
        .scalar() or 0,
        recent_users=db.query(User).order_by(User.created_at.desc(), User.id.desc()).limit(5).all(),
    )


@router.get("", response_model=list[AdminUserResponse])
def list_users(
    response: Response,
    q: str | None = Query(None, max_length=255),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    query = db.query(User)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(User.email.ilike(term), User.username.ilike(term), User.full_name.ilike(term)))
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))

    total = query.count()
    response.headers["X-Total-Count"] = str(total)
    return query.order_by(User.created_at.desc(), User.id.desc()).offset((page - 1) * size).limit(size).all()


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: AdminUserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    email = str(body.email).lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email đã được sử dụng")
    if db.query(User).filter(func.lower(User.username) == body.username.lower()).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tên đăng nhập đã được sử dụng")

    user = User(
        email=email,
        username=body.username,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        system_role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tài khoản không tồn tại")
    user.full_name = body.full_name
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=AdminUserResponse)
def update_user_status(
    user_id: int,
    update: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tài khoản không tồn tại")
    if user.system_role == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể khoá hoặc mở khoá tài khoản admin")
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể thay đổi trạng thái tài khoản của chính mình")

    user.is_active = update.is_active
    db.commit()
    db.refresh(user)
    return user
