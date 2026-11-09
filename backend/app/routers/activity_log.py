from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.core.permissions import get_project_and_membership
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.activity_log import ActivityLogResponse

router = APIRouter(prefix="/projects/{project_id}/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=List[ActivityLogResponse])
def list_activity_logs(
    project_id: int,
    response: Response,
    db: Session = Depends(get_db),
    data: tuple = Depends(get_project_and_membership),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    task_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """Lịch sử hoạt động của dự án"""
    project, member = data

    query = db.query(ActivityLog).filter(ActivityLog.project_id == project_id)

    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type)
    if action:
        query = query.filter(ActivityLog.action == action)
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    if task_id:
        query = query.filter(ActivityLog.task_id == task_id)
    if date_from:
        query = query.filter(ActivityLog.created_at >= date_from)
    if date_to:
        query = query.filter(ActivityLog.created_at <= date_to)

    query = query.order_by(ActivityLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * size).limit(size).all()

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Size"] = str(size)
    response.headers["X-Total-Pages"] = str((total + size - 1) // size)

    result = []
    for log in logs:
        result.append(ActivityLogResponse(
            id=log.id,
            project_id=log.project_id,
            task_id=log.task_id,
            user_id=log.user_id,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            action=log.action,
            old_value=log.old_value,
            new_value=log.new_value,
            created_at=log.created_at,
            user_email=log.user.email if log.user else None,
            user_full_name=log.user.full_name if log.user else None,
        ))
    return result