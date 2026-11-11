from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Kiểm tra FastAPI và MySQL để frontend báo đúng trạng thái kết nối."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend đang chạy nhưng không kết nối được MySQL.",
        ) from error
    return {"status": "ok", "database": "connected"}

