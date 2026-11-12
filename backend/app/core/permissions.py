"""Phân quyền theo vai trò trong project_members.

Vai trò (role): owner > manager > member > viewer.
Quy ước: thao tác đọc cần >= member, thao tác ghi (CRUD lists/tasks...) cần >= manager.

Hiện dự án chưa có trang đăng nhập, nên user_id lấy từ header `X-User-Id`.
Khi nhóm làm chức năng login, chỉ cần sửa hàm get_current_user_id
(trả về user thật sau khi decode token) — phần còn lại giữ nguyên.
"""
from fastapi import Depends, Header, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project_member import ProjectMember

ROLE_LEVEL = {"viewer": 1, "member": 2, "manager": 3, "owner": 4}


def get_current_user_id(x_user_id: int | None = Header(default=None)) -> int:
    """Lấy id user đang gọi API. Thay bằng decode JWT khi có login."""
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu header X-User-Id (chưa đăng nhập)",
        )
    return x_user_id


def require_role(minimum_role: str):
    """Dependency factory: kiểm tra user có role đủ cao trong project :project_id."""
    minimum_level = ROLE_LEVEL[minimum_role]

    def checker(
        project_id: int = Path(...),
        user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
    ) -> ProjectMember:
        membership = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        if membership is None:
            raise HTTPException(status_code=403, detail="Bạn không thuộc project này")
        if ROLE_LEVEL[membership.role] < minimum_level:
            raise HTTPException(
                status_code=403,
                detail=f"Cần vai trò {minimum_role} trở lên (bạn là {membership.role})",
            )
        return membership

    return checker
