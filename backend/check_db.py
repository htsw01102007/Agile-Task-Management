import pymysql
from app.core.config import settings

try:
    connection = pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        port=settings.DB_PORT
    )
    print("Kết nối thành công tới MySQL!")
    connection.close()
except Exception as e:
    print(f"Kết nối thất bại: {e}")
