"""Seed dữ liệu mẫu: users, project, members (4 vai trò), lists, tasks, assignees.

Cách chạy (trong thư mục backend/):
    ./venv/bin/python scripts/seed_demo.py

Xoá sạch dữ liệu cũ rồi tạo mới — an toàn để chạy lại nhiều lần.
Sau khi chạy xong:
    User ID  1 = An  (owner)   -> làm được mọi thứ
    User ID  2 = Binh (manager) -> CRUD list/task
    User ID  3 = Chi  (member)  -> chỉ đọc
    User ID  4 = Dung (viewer)  -> chỉ đọc, bị chặn khi ghi
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta

from sqlalchemy import text

from app.db.session import engine

DATA = {
    "users": [
        {"email": "an@example.com", "name": "An (owner)"},
        {"email": "binh@example.com", "name": "Binh (manager)"},
        {"email": "chi@example.com", "name": "Chi (member)"},
        {"email": "dung@example.com", "name": "Dung (viewer)"},
    ],
    "roles": ["owner", "manager", "member", "viewer"],
    "lists": ["Viec can lam", "Dang lam", "Hoan thanh"],
    "tasks": [
        # (title, list_index, priority, days_until_due, done, assignee_user_index)
        ("Thiết kế giao diện login", 0, "high", 3, False, 1),
        ("Viết API đăng nhập", 0, "urgent", 2, False, 2),
        ("Chuẩn hoá cấu trúc DB", 0, "medium", None, False, None),
        ("Code trang dashboard", 1, "high", 5, False, 1),
        ("Kiểm thử phân quyền", 1, "medium", None, False, None),
        ("Deploy lên server thử", 1, "low", 10, False, None),
        ("Họp tổng kết tuần 1", 2, "low", None, True, 3),
        ("Sửa lỗi CORS", 2, "high", None, True, 2),
    ],
}


def main() -> None:
    with engine.begin() as conn:
        # Xoá sạch (thứ tự con -> cha để tránh vi phạm FK)
        for table in [
            "task_assignees",
            "task_labels",
            "checklist_items",
            "comments",
            "attachments",
            "activity_logs",
            "tasks",
            "lists",
            "project_members",
            "projects",
            "labels",
            "users",
        ]:
            conn.execute(text(f"DELETE FROM {table}"))
        conn.execute(text("ALTER TABLE users AUTO_INCREMENT = 1"))
        conn.execute(text("ALTER TABLE projects AUTO_INCREMENT = 1"))
        conn.execute(text("ALTER TABLE lists AUTO_INCREMENT = 1"))
        conn.execute(text("ALTER TABLE tasks AUTO_INCREMENT = 1"))
        conn.execute(text("ALTER TABLE task_assignees AUTO_INCREMENT = 1"))

        # Users (password_hash giả lập — chưa có module login)
        for u in DATA["users"]:
            conn.execute(
                text(
                    "INSERT INTO users (email, password_hash, full_name, is_active) "
                    "VALUES (:email, 'seed-hash', :name, 1)"
                ),
                u,
            )

        # Project + members: user i có role DATA["roles"][i] (id 1..4)
        conn.execute(
            text(
                "INSERT INTO projects (name, description, owner_id, is_archived) "
                "VALUES ('Du an mau', 'Project demo co assignee + phan quyen', 1, 0)"
            )
        )
        for i, role in enumerate(DATA["roles"], start=1):
            conn.execute(
                text(
                    "INSERT INTO project_members (project_id, user_id, role) "
                    "VALUES (1, :uid, :r)"
                ),
                {"uid": i, "r": role},
            )

        # Lists
        for pos, name in enumerate(DATA["lists"], start=1):
            conn.execute(
                text(
                    "INSERT INTO lists (project_id, name, position, is_done_column) "
                    "VALUES (1, :n, :p, :d)"
                ),
                {"n": name, "p": pos, "d": 1 if pos == 3 else 0},
            )

        # Tasks + assignees
        for idx, (title, li, prio, days, done, assignee) in enumerate(
            DATA["tasks"], start=1
        ):
            due = (
                (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
                if days is not None
                else None
            )
            params = {
                "t": title,
                "lid": li + 1,
                "p": prio,
                "d": due,
                "done": datetime.now() if done else None,
                "pos": idx,
            }
            task_id = conn.execute(
                text(
                    "INSERT INTO tasks (project_id, list_id, title, priority, position, "
                    "due_date, completed_at, created_by, is_deleted) "
                    "VALUES (1, :lid, :t, :p, :pos, :d, :done, 1, 0)"
                ),
                params,
            ).lastrowid
            if assignee:
                conn.execute(
                    text(
                        "INSERT INTO task_assignees (task_id, user_id) VALUES (:t, :u)"
                    ),
                    {"t": task_id, "u": assignee},
                )

    print("Seed xong!")
    print("  users: An(1, owner) Binh(2, manager) Chi(3, member) Dung(4, viewer)")
    print(
        "  project 1 'Du an mau' | lists: 1 Viec can lam, 2 Dang lam, 3 Hoan thanh(done)"
    )
    print(f"  {len(DATA['tasks'])} tasks (6 dang lam + 2 hoan thanh), co assignee")
    print("Header test: X-User-Id: 1|2|3|4")


if __name__ == "__main__":
    main()
