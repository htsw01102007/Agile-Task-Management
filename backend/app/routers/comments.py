"""Bình luận trên task: thêm, trả lời, sửa và xoá mềm bình luận của chính mình."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.crud import comment as comment_crud
from app.crud.comment import CommentActionError
from app.db.database import get_db
from app.models.entities import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(tags=["Comments"])

_COMMENT_ERRORS = {
    "parent_not_found": (status.HTTP_404_NOT_FOUND, "Không tìm thấy bình luận cần trả lời"),
    "parent_other_task": (status.HTTP_400_BAD_REQUEST, "Chỉ trả lời bình luận thuộc cùng task"),
    "reply_to_reply": (status.HTTP_400_BAD_REQUEST, "Chỉ trả lời được bình luận gốc"),
    "parent_deleted": (status.HTTP_400_BAD_REQUEST, "Không trả lời bình luận đã xoá"),
    "missing_after_create": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Không đọc lại được bình luận vừa tạo"),
    "missing_after_update": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Không đọc lại được bình luận vừa sửa"),
    "missing_after_delete": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Không đọc lại được bình luận vừa xoá"),
}


def _raise_comment_error(error: CommentActionError) -> None:
    status_code, detail = _COMMENT_ERRORS.get(
        error.code,
        (status.HTTP_400_BAD_REQUEST, "Không xử lý được bình luận"),
    )
    raise HTTPException(status_code=status_code, detail=detail)


def _own_comment_or_http(comment, current_user: User):
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bình luận")
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn chỉ sửa hoặc xoá được bình luận của mình",
        )
    if comment.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bình luận đã được xoá")
    return comment


@router.get("/tasks/{task_id}/comments", response_model=list[CommentResponse])
def list_comments(
    task_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    task = comment_crud.get_visible_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy task")
    return comment_crud.list_task_comments(db, task.id)


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    task_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = comment_crud.get_visible_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy task")
    try:
        return comment_crud.create_comment(db, task, current_user, data)
    except CommentActionError as error:
        db.rollback()
        _raise_comment_error(error)


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = _own_comment_or_http(comment_crud.get_comment(db, comment_id), current_user)
    try:
        return comment_crud.update_own_comment(db, comment, data.content)
    except CommentActionError as error:
        db.rollback()
        _raise_comment_error(error)


@router.delete("/comments/{comment_id}", response_model=CommentResponse)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = _own_comment_or_http(comment_crud.get_comment(db, comment_id), current_user)
    try:
        return comment_crud.soft_delete_own_comment(db, comment, current_user.id)
    except CommentActionError as error:
        db.rollback()
        _raise_comment_error(error)
