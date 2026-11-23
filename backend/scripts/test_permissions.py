"""Ma trận phân quyền: chạy mọi API list/task theo 4 vai trò.

Chạy: ./venv/bin/python scripts/test_permissions.py   (server phải đang chạy :8000)
In bảng PASS/FAIL; exit 1 nếu có FAIL.
"""

import json
import sys
import urllib.error
import urllib.request

B = "http://127.0.0.1:8000/api"

# user_id 1=An owner, 2=Binh manager, 3=Chi member, 4=Dung viewer
USERS = {1: "owner", 2: "manager", 3: "member", 4: "viewer"}
# Vai trò tối thiểu theo từng hành động (theo spec: ghi = manager+, đọc = member+)
WRITE = "manager"
READ = "member"

LEVEL = {"viewer": 0, "member": 1, "manager": 2, "owner": 3}


def call(method, path, user_id, body=None):
    req = urllib.request.Request(
        B + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"X-User-Id": str(user_id), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def expect(role, action):
    """"Trạng thái kỳ vọng: 2xx nếu role đủ quyền, 401/403 nếu không."""
    minimum = WRITE if action.startswith("WRITE") else READ
    return "ok" if LEVEL[role] >= LEVEL[minimum] else "denied"


RESULTS = []


def check(action, method, path, user_id, body=None, personal=False):
    role = USERS[user_id]
    if personal:
        # API cá nhân (my-tasks): mọi user đều xem được việc của chính mình
        status = call(method, path, user_id, body)
        passed = 200 <= status < 300
    else:
        want = expect(role, action)
        status = call(method, path, user_id, body)
        allowed = 200 <= status < 300
        passed = allowed if want == "ok" else status in (401, 403)
    RESULTS.append(
        (f"{action} [{role}]", method, path, status, "PASS" if passed else "FAIL")
    )


def main():
    # ---- LISTS ----
    check("READ lists", "GET", "/projects/1/lists", 3)  # member đọc OK
    check("READ lists", "GET", "/projects/1/lists", 4)  # viewer đọc OK
    check(
        "WRITE create list", "POST", "/projects/1/lists", 2, {"name": "List thử"}
    )  # manager OK
    check(
        "WRITE create list", "POST", "/projects/1/lists", 3, {"name": "List bị chặn"}
    )  # member 403
    check(
        "WRITE create list", "POST", "/projects/1/lists", 4, {"name": "List bị chặn"}
    )  # viewer 403
    check(
        "WRITE rename list",
        "PUT",
        "/projects/1/lists/1",
        2,
        {"name": "Viec can lam moi"},
    )
    check("WRITE rename list", "PUT", "/projects/1/lists/1", 3, {"name": "X"})
    check("WRITE reorder", "PUT", "/projects/1/lists/reorder", 2, {"ids": [1, 2, 3]})
    check("WRITE reorder", "PUT", "/projects/1/lists/reorder", 4, {"ids": [2, 1, 3]})
    check("WRITE mark done", "PUT", "/projects/1/lists/1/done", 2)
    check("WRITE mark done", "PUT", "/projects/1/lists/1/done", 4)

    # ---- TASKS (list 1 thuộc project 1) ----
    check("READ tasks", "GET", "/lists/1/tasks", 3)
    check("READ tasks", "GET", "/lists/1/tasks", 4)
    check("WRITE create task", "POST", "/lists/1/tasks", 2, {"title": "Task m"})
    check("WRITE create task", "POST", "/lists/1/tasks", 3, {"title": "Blocked"})
    check("WRITE create task", "POST", "/lists/1/tasks", 4, {"title": "Blocked"})
    check("WRITE update task", "PATCH", "/tasks/1", 2, {"title": "Sua OK"})
    check("WRITE update task", "PATCH", "/tasks/1", 3, {"title": "Blocked"})
    check("WRITE delete task", "DELETE", "/tasks/2", 2)
    check("WRITE delete task", "DELETE", "/tasks/3", 4)

    # ---- ASSIGNEES ----
    check("READ assignees", "GET", "/tasks/1/assignees", 3)
    check("WRITE assign", "PUT", "/tasks/1/assignees", 2, {"user_id": 3})
    check("WRITE assign", "PUT", "/tasks/1/assignees", 3, {"user_id": 3})
    check("READ my-tasks", "GET", "/my-tasks", 4, personal=True)  # xem việc của chính mình

    # ---- SEARCH + phân trang ----
    check("READ search", "GET", "/projects/1/tasks/search?page=1", 3)
    check("READ search", "GET", "/projects/1/tasks/search?priority=high", 4)

    # In kết quả
    print(f"{'Hành động':<28} {'METHOD':<7} {'HTTP':>4}  Kết quả")
    print("-" * 70)
    fails = 0
    for action, method, path, status, verdict in RESULTS:
        if verdict == "FAIL":
            fails += 1
        print(f"{action:<28} {method:<7} {status:>4}  {verdict}")
    print("-" * 70)
    print(f"Tổng: {len(RESULTS)} | FAIL: {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
