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

