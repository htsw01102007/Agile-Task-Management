from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime, timezone

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.permissions import get_project_and_membership, require_project_roles
from app.core.ws_manager import notify_project_sync
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.list import ListModel
from app.models.task import Task
from app.crud.project import create_project_with_owner, query_active_projects
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse
from app.schemas.list import ListResponse, ListCreate, ListUpdate, ListReorder

router = APIRouter(prefix="/projects", tags=["Projects"])


def _renumber_project_lists(db: Session, project_id: int) -> List[ListModel]:
    """Đánh số lại position của các list trong dự án liên tục từ 0, 1, 2..."""
    lists = (
        db.query(ListModel)
        .filter(ListModel.project_id == project_id)
        .order_by(ListModel.position.asc(), ListModel.id.asc())
        .all()
    )
    for idx, item in enumerate(lists):
        item.position = idx
    return lists


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_project_with_owner(db=db, project_in=project_in, owner_id=current_user.id)


@router.get("", response_model=List[ProjectResponse])
def list_my_projects(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, pattern="^(active|completed|archived)$"),
):
    """Danh sách dự án mà người dùng hiện tại là thành viên (chưa bị xoá mềm), có phân trang và lọc trạng thái"""
    query = (
        query_active_projects(db)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(ProjectMember.user_id == current_user.id)
    )
    if status:
        query = query.filter(Project.status == status)

    total = query.count()
    projects = query.order_by(Project.created_at.desc(), Project.id.desc()).offset(skip).limit(limit).all()
    response.headers["X-Total-Count"] = str(total)
    return projects


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(get_project_and_membership),
):
    project, member = data
    response = ProjectDetailResponse.model_validate(project)
    response.member_count = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).count()
    response.user_role = member.role

    active_tasks_query = db.query(Task).filter(Task.project_id == project_id, Task.is_deleted.is_(False))
    task_count = active_tasks_query.count()
    completed_task_count = active_tasks_query.filter(Task.completed_at.isnot(None)).count()
    completion_rate = round((completed_task_count / task_count) * 100, 2) if task_count > 0 else 0.0

    response.task_count = task_count
    response.completed_task_count = completed_task_count
    response.completion_rate = completion_rate
    return response


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(
        require_project_roles("owner", "manager", allow_read_only_when_inactive=True)
    ),
):
    project, _ = data

    update_data = project_update.model_dump(exclude_unset=True)

    # Dự án completed/archived là chỉ đọc: chỉ cho phép đổi trạng thái.
    # Muốn sửa các trường khác phải mở lại 'active' (có thể gửi kèm trong cùng request).
    if project.status in ("completed", "archived") and update_data.get("status") != "active":
        non_status_fields = {k for k in update_data.keys() if k != "status"}
        if non_status_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dự án đang ở trạng thái '{project.status}' (chỉ đọc), hãy mở lại trạng thái 'active' trước khi chỉnh sửa",
            )

    new_start = update_data.get("start_date", project.start_date)
    new_end = update_data.get("end_date", project.end_date)
    if new_start and new_end and new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày kết thúc không được sớm hơn ngày bắt đầu",
        )

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(
        require_project_roles("owner", allow_read_only_when_inactive=True)
    ),
):
    project, _ = data
    project.deleted_at = func.now()
    db.commit()
    return None


# ===== BOARD & LIST ENDPOINTS =====

@router.get("/{project_id}/lists", response_model=List[ListResponse])
def list_project_lists(
    project_id: int,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(get_project_and_membership),
):
    project, _ = data
    lists = (
        db.query(ListModel)
        .filter(ListModel.project_id == project_id)
        .order_by(ListModel.position.asc(), ListModel.id.asc())
        .all()
    )
    return lists


@router.post("/{project_id}/lists", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
def create_list(
    project_id: int,
    list_in: ListCreate,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    project, _ = data

    existing_lists = (
        db.query(ListModel)
        .filter(ListModel.project_id == project_id)
        .order_by(ListModel.position.asc(), ListModel.id.asc())
        .all()
    )

    is_done = bool(list_in.is_done_column)
    if not existing_lists:
        # Nếu dự án chưa có cột nào, cột đầu tiên mặc định cần đảm bảo có cột hoàn thành
        is_done = bool(list_in.is_done_column)

    if is_done:
        # Đảm bảo mỗi dự án chỉ có đúng 1 cột hoàn thành
        db.query(ListModel).filter(
            ListModel.project_id == project_id,
            ListModel.is_done_column.is_(True),
        ).update({ListModel.is_done_column: False}, synchronize_session=False)

    target_pos = list_in.position if list_in.position is not None else len(existing_lists)
    target_pos = max(0, min(target_pos, len(existing_lists)))

    for item in existing_lists:
        if item.position >= target_pos:
            item.position += 1

    new_list = ListModel(
        project_id=project.id,
        name=list_in.name,
        position=target_pos,
        is_done_column=is_done,
    )
    db.add(new_list)
    db.flush()
    _renumber_project_lists(db, project_id)
    db.commit()
    db.refresh(new_list)

    notify_project_sync(
        project_id,
        "list_created",
        ListResponse.model_validate(new_list).model_dump(mode="json"),
    )
    return new_list


@router.patch("/{project_id}/lists/reorder", response_model=List[ListResponse])
def reorder_lists(
    project_id: int,
    reorder_in: ListReorder,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    """Sắp xếp lại thứ tự các list trong bảng và đánh số lại liên tục từ 0"""
    project, _ = data

    lists = db.query(ListModel).filter(ListModel.project_id == project_id).all()
    list_map = {lst.id: lst for lst in lists}

    if len(reorder_in.list_ids) != len(lists) or set(reorder_in.list_ids) != set(list_map.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách list_ids phải chứa đầy đủ tất cả các cột của dự án",
        )

    for idx, lid in enumerate(reorder_in.list_ids):
        list_map[lid].position = idx

    db.commit()
    ordered = (
        db.query(ListModel)
        .filter(ListModel.project_id == project_id)
        .order_by(ListModel.position.asc())
        .all()
    )
    notify_project_sync(
        project_id,
        "list_reordered",
        [ListResponse.model_validate(x).model_dump(mode="json") for x in ordered],
    )
    return ordered


@router.put("/{project_id}/lists/{list_id}", response_model=ListResponse)
def update_list(
    project_id: int,
    list_id: int,
    list_update: ListUpdate,
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    project, _ = data
    lst = (
        db.query(ListModel)
        .filter(ListModel.id == list_id, ListModel.project_id == project_id)
        .first()
    )
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Danh sách không tồn tại")

    update_data = list_update.model_dump(exclude_unset=True)

    # Xử lý đánh dấu cột hoàn thành (mỗi dự án đúng một cột is_done_column)
    if "is_done_column" in update_data:
        new_is_done = update_data["is_done_column"]
        if new_is_done is False and lst.is_done_column:
            other_done = (
                db.query(ListModel)
                .filter(
                    ListModel.project_id == project_id,
                    ListModel.id != list_id,
                    ListModel.is_done_column.is_(True),
                )
                .first()
            )
            if not other_done:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mỗi dự án phải có đúng một cột hoàn thành. Hãy đặt cột khác làm cột hoàn thành trước.",
                )
        elif new_is_done is True and not lst.is_done_column:
            db.query(ListModel).filter(
                ListModel.project_id == project_id,
                ListModel.id != list_id,
                ListModel.is_done_column.is_(True),
            ).update({ListModel.is_done_column: False}, synchronize_session=False)
            lst.is_done_column = True
            # Tự cập nhật completed_at cho các task đang ở trong cột hoàn thành mới này
            now = datetime.now(timezone.utc)
            db.query(Task).filter(
                Task.list_id == list_id,
                Task.is_deleted.is_(False),
                Task.completed_at.is_(None),
            ).update({Task.completed_at: now}, synchronize_session=False)

    if "name" in update_data and update_data["name"] is not None:
        lst.name = update_data["name"]

    if "position" in update_data and update_data["position"] is not None:
        new_pos = max(0, update_data["position"])
        other_lists = (
            db.query(ListModel)
            .filter(ListModel.project_id == project_id, ListModel.id != list_id)
            .order_by(ListModel.position.asc(), ListModel.id.asc())
            .all()
        )
        new_pos = min(new_pos, len(other_lists))
        other_lists.insert(new_pos, lst)
        for idx, item in enumerate(other_lists):
            item.position = idx

    db.commit()
    db.refresh(lst)

    notify_project_sync(
        project_id,
        "list_updated",
        ListResponse.model_validate(lst).model_dump(mode="json"),
    )
    return lst


@router.delete("/{project_id}/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    project_id: int,
    list_id: int,
    target_list_id: Optional[int] = Query(
        None,
        description="ID danh sách đích để chuyển các task sang nếu danh sách cần xoá đang có task",
    ),
    db: Session = Depends(get_db),
    data: tuple[Project, ProjectMember] = Depends(require_project_roles("owner", "manager")),
):
    """
    Xoá danh sách (list) trong dự án:
    - Không cho phép xoá cột hoàn thành duy nhất.
    - Nếu list có task đang hoạt động, bắt buộc truyền target_list_id để chuyển task sang list đích.
    - Đánh số lại position của các list còn lại liên tục từ 0.
    """
    project, _ = data
    lst = (
        db.query(ListModel)
        .filter(ListModel.id == list_id, ListModel.project_id == project_id)
        .first()
    )
    if not lst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Danh sách không tồn tại")

    if lst.is_done_column:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể xoá cột hoàn thành duy nhất của dự án",
        )

    active_tasks = (
        db.query(Task)
        .filter(Task.list_id == list_id, Task.is_deleted.is_(False))
        .order_by(Task.position.asc())
        .all()
    )

    if active_tasks and target_list_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Danh sách đang chứa công việc. Vui lòng truyền target_list_id để chuyển công việc sang danh sách khác trước khi xoá.",
        )

    target_list: Optional[ListModel] = None
    if target_list_id is not None:
        if target_list_id == list_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Danh sách đích phải khác danh sách cần xoá",
            )
        target_list = (
            db.query(ListModel)
            .filter(ListModel.id == target_list_id, ListModel.project_id == project_id)
            .first()
        )
        if not target_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Danh sách đích không tồn tại trong dự án",
            )

    # Nếu có task (kể cả đã xoá mềm) trong list này, chuyển sang target_list hoặc cột còn lại để bảo toàn FK
    all_tasks_in_list = db.query(Task).filter(Task.list_id == list_id).order_by(Task.position.asc()).all()
    if all_tasks_in_list:
        if not target_list:
            target_list = (
                db.query(ListModel)
                .filter(ListModel.project_id == project_id, ListModel.id != list_id)
                .order_by(ListModel.position.asc())
                .first()
            )
        if not target_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xoá danh sách duy nhất của dự án",
            )

        max_pos_row = (
            db.query(Task.position)
            .filter(Task.list_id == target_list.id, Task.is_deleted.is_(False))
            .order_by(Task.position.desc())
            .first()
        )
        next_pos = (max_pos_row[0] + 1) if max_pos_row else 0
        now = datetime.now(timezone.utc)

        for t in all_tasks_in_list:
            t.list_id = target_list.id
            if not t.is_deleted:
                t.position = next_pos
                next_pos += 1
                if target_list.is_done_column and not t.completed_at:
                    t.completed_at = now
                elif not target_list.is_done_column and t.completed_at:
                    t.completed_at = None
        db.flush()
        db.expire(lst, ["tasks"])

    db.delete(lst)
    db.flush()
    _renumber_project_lists(db, project_id)
    db.commit()

    notify_project_sync(
        project_id,
        "list_deleted",
        {"list_id": list_id, "target_list_id": target_list.id if target_list else None},
    )
    return None
