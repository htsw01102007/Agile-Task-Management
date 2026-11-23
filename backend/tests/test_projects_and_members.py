def test_project_crud_my_role_and_member_permissions(client, test_user_factory):
    owner = test_user_factory("owner")
    member = test_user_factory("member")
    viewer = test_user_factory("viewer")

    # Create project
    proj_resp = client.post(
        "/api/projects",
        headers=owner["headers"],
        json={"name": "Pytest Agile Project", "description": "Automated test"},
    )
    assert proj_resp.status_code == 201, proj_resp.text
    project_id = proj_resp.json()["id"]
    test_user_factory.track_project(project_id)
    assert proj_resp.json()["my_role"] == "owner"

    # Add member and viewer via invitation flow
    test_user_factory.invite_member(owner["headers"], project_id, member, role="member")
    test_user_factory.invite_member(owner["headers"], project_id, viewer, role="viewer")

    # Each user sees their own my_role in list & detail
    list_v = client.get("/api/projects", headers=viewer["headers"]).json()
    matched = [p for p in list_v if p["id"] == project_id]
    assert len(matched) == 1
    assert matched[0]["my_role"] == "viewer"

    detail_m = client.get(f"/api/projects/{project_id}", headers=member["headers"])
    assert detail_m.status_code == 200
    assert detail_m.json()["my_role"] == "member"

    # List trả về member_count/task_count khớp endpoint detail
    lists = client.get(f"/api/projects/{project_id}/lists", headers=owner["headers"]).json()
    assert client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={"title": "Counted task", "list_id": lists[0]["id"]},
    ).status_code == 201
    list_o = client.get("/api/projects", headers=owner["headers"]).json()
    mine = next(p for p in list_o if p["id"] == project_id)
    assert mine["member_count"] == 3  # owner + member + viewer
    assert mine["task_count"] == 1

    # Member cannot update project or add members
    assert client.put(
        f"/api/projects/{project_id}",
        headers=member["headers"],
        json={"name": "Blocked"},
    ).status_code == 403

    # Viewer cannot create lists
    assert client.post(
        f"/api/projects/{project_id}/lists",
        headers=viewer["headers"],
        json={"name": "Blocked List"},
    ).status_code == 403

    # Frontend connection endpoints: /projects/summary, /projects/dashboard/summary, /projects/{id}/board, /tasks/deleted
    summary_resp = client.get("/api/projects/summary?skip=0&limit=1", headers=owner["headers"])
    assert summary_resp.status_code == 200
    assert summary_resp.headers["X-Total-Count"]
    assert any(p["id"] == project_id and p["user_role"] == "owner" for p in summary_resp.json())

    dash_resp = client.get("/api/projects/dashboard/summary", headers=owner["headers"])
    assert dash_resp.status_code == 200
    assert "active_project_count" in dash_resp.json()

    board_resp = client.get(f"/api/projects/{project_id}/board?skip=0&limit=1", headers=owner["headers"])
    assert board_resp.status_code == 200
    assert board_resp.headers["X-Total-Tasks"] == "1"
    assert "lists" in board_resp.json() and "tasks" in board_resp.json()

    deleted_resp = client.get(f"/api/projects/{project_id}/tasks/deleted", headers=owner["headers"])
    assert deleted_resp.status_code == 200
    assert isinstance(deleted_resp.json(), list)

    # Non-admin cannot access /api/admin/users
    assert client.get("/api/admin/users", headers=owner["headers"]).status_code == 403



def test_project_stats_endpoint(client, test_user_factory):
    from datetime import datetime, timedelta, timezone

    owner = test_user_factory("stats_owner")
    member = test_user_factory("stats_member")
    viewer = test_user_factory("stats_viewer")
    outsider = test_user_factory("stats_outsider")

    proj_resp = client.post(
        "/api/projects",
        headers=owner["headers"],
        json={"name": "Stats Test Project"},
    )
    assert proj_resp.status_code == 201, proj_resp.text
    project_id = proj_resp.json()["id"]
    test_user_factory.track_project(project_id)

    test_user_factory.invite_member(owner["headers"], project_id, member, role="member")
    test_user_factory.invite_member(owner["headers"], project_id, viewer, role="viewer")

    lists = client.get(f"/api/projects/{project_id}/lists", headers=owner["headers"]).json()
    todo_list = lists[0]
    in_progress_list = lists[1]
    done_list = next(l for l in lists if l["is_done_column"])

    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    future_due = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    # 1) Overdue task in todo, assigned to member
    assert client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={
            "title": "Overdue Task",
            "list_id": todo_list["id"],
            "priority": "urgent",
            "due_date": past_due,
            "assignee_ids": [member["id"]],
        },
    ).status_code == 201

    # 2) Active task in in_progress, assigned to owner & member
    assert client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={
            "title": "Active Task",
            "list_id": in_progress_list["id"],
            "due_date": future_due,
            "assignee_ids": [owner["id"], member["id"]],
        },
    ).status_code == 201

    # 3) Completed task in done list with past due_date (should NOT count as overdue)
    assert client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={
            "title": "Done Task",
            "list_id": done_list["id"],
            "due_date": past_due,
            "assignee_ids": [owner["id"]],
        },
    ).status_code == 201

    # 4) Unassigned task in todo
    assert client.post(
        f"/api/projects/{project_id}/tasks",
        headers=owner["headers"],
        json={"title": "Unassigned Task", "list_id": todo_list["id"]},
    ).status_code == 201

    # Viewer can fetch stats; outsider cannot
    assert client.get(f"/api/projects/{project_id}/stats", headers=outsider["headers"]).status_code in (403, 404)
    stats_resp = client.get(f"/api/projects/{project_id}/stats", headers=viewer["headers"])
    assert stats_resp.status_code == 200, stats_resp.text
    stats = stats_resp.json()

    assert stats["total_tasks"] == 4
    assert stats["completed_tasks"] == 1
    assert stats["in_progress_tasks"] == 3
    assert stats["overdue_tasks"] == 1
    assert stats["unassigned_tasks"] == 1
    assert stats["completion_rate"] == 25.0

    # Check by_status
    status_by_id = {s["list_id"]: s for s in stats["by_status"]}
    assert status_by_id[todo_list["id"]]["task_count"] == 2
    assert status_by_id[in_progress_list["id"]]["task_count"] == 1
    assert status_by_id[done_list["id"]]["task_count"] == 1
    assert status_by_id[done_list["id"]]["is_done_column"] is True

    # Check overdue_task_items
    assert len(stats["overdue_task_items"]) == 1
    assert stats["overdue_task_items"][0]["title"] == "Overdue Task"

    # Check by_member
    member_by_id = {m["user_id"]: m for m in stats["by_member"]}
    assert member_by_id[owner["id"]]["total_tasks"] == 2
    assert member_by_id[owner["id"]]["completed_tasks"] == 1
    assert member_by_id[owner["id"]]["overdue_tasks"] == 0
    assert member_by_id[owner["id"]]["completion_rate"] == 50.0

    assert member_by_id[member["id"]]["total_tasks"] == 2
    assert member_by_id[member["id"]]["completed_tasks"] == 0
    assert member_by_id[member["id"]]["overdue_tasks"] == 1

    assert member_by_id[viewer["id"]]["total_tasks"] == 0
