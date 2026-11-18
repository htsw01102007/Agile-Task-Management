from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.project_invitation import ProjectInvitation
from app.models.project_member import ProjectMember


def _create_project(client, test_user_factory, owner):
    resp = client.post("/api/projects", headers=owner["headers"], json={"name": "Invitation Project"})
    assert resp.status_code == 201, resp.text
    project_id = resp.json()["id"]
    test_user_factory.track_project(project_id)
    return project_id


def _invite(client, owner, project_id, email, role="member"):
    return client.post(
        f"/api/projects/{project_id}/invitations",
        headers=owner["headers"],
        json={"invitee_email": email, "role": role},
    )


def test_invitation_token_status_and_7_day_expiry(client, test_user_factory):
    owner = test_user_factory("invown")
    invitee = test_user_factory("invitee")
    project_id = _create_project(client, test_user_factory, owner)

    resp = _invite(client, owner, project_id, invitee["email"])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["raw_token"]
    assert len(body["token"]) == 64  # chỉ lưu bản băm SHA-256
    assert body["token"] != body["raw_token"]

    expires_at = datetime.fromisoformat(body["expires_at"])
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = expires_at - now_utc
    assert timedelta(days=6, hours=23) <= delta <= timedelta(days=7, minutes=5)


def test_block_duplicate_pending_and_existing_member(client, test_user_factory):
    owner = test_user_factory("dupown")
    invitee = test_user_factory("dupinv")
    project_id = _create_project(client, test_user_factory, owner)

    assert _invite(client, owner, project_id, invitee["email"]).status_code == 201
    # Trùng lời mời đang chờ (kể cả khác hoa/thường)
    dup = _invite(client, owner, project_id, invitee["email"].upper())
    assert dup.status_code == 400

    # Không mời chính owner (đã là thành viên)
    self_inv = _invite(client, owner, project_id, owner["email"])
    assert self_inv.status_code == 400


def test_accept_adds_member_and_cannot_reuse(client, test_user_factory):
    owner = test_user_factory("accown")
    invitee = test_user_factory("accinv")
    project_id = _create_project(client, test_user_factory, owner)

    raw = _invite(client, owner, project_id, invitee["email"], role="viewer").json()["raw_token"]

    # Người khác không được dùng lời mời
    stranger = test_user_factory("accstr")
    assert client.post(f"/api/invitations/accept/{raw}", headers=stranger["headers"]).status_code == 403

    acc = client.post(f"/api/invitations/accept/{raw}", headers=invitee["headers"])
    assert acc.status_code == 200, acc.text
    assert acc.json()["project_id"] == project_id

    db = SessionLocal()
    try:
        member = db.query(ProjectMember).filter_by(project_id=project_id, user_id=invitee["id"]).first()
        assert member is not None and member.role == "viewer"
        inv = db.query(ProjectInvitation).filter_by(project_id=project_id, invitee_email=invitee["email"]).first()
        assert inv.status == "accepted" and inv.responded_at is not None
    finally:
        db.close()

    # Chấp nhận lần 2 bị chặn
    assert client.post(f"/api/invitations/accept/{raw}", headers=invitee["headers"]).status_code == 400
    # Đã là thành viên -> không mời lại được
    assert _invite(client, owner, project_id, invitee["email"]).status_code == 400


def test_decline_and_reinvite(client, test_user_factory):
    owner = test_user_factory("decown")
    invitee = test_user_factory("decinv")
    project_id = _create_project(client, test_user_factory, owner)

    raw = _invite(client, owner, project_id, invitee["email"]).json()["raw_token"]
    dec = client.post(f"/api/invitations/decline/{raw}", headers=invitee["headers"])
    assert dec.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(ProjectMember).filter_by(project_id=project_id, user_id=invitee["id"]).first() is None
    finally:
        db.close()

    assert client.post(f"/api/invitations/accept/{raw}", headers=invitee["headers"]).status_code == 400
    # Sau khi từ chối có thể mời lại
    assert _invite(client, owner, project_id, invitee["email"]).status_code == 201


def test_expired_invitation_cannot_be_accepted_and_allows_reinvite(client, test_user_factory):
    owner = test_user_factory("expown")
    invitee = test_user_factory("expinv")
    project_id = _create_project(client, test_user_factory, owner)

    body = _invite(client, owner, project_id, invitee["email"]).json()

    db = SessionLocal()
    try:
        inv = db.query(ProjectInvitation).filter_by(id=body["id"]).first()
        inv.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    acc = client.post(f"/api/invitations/accept/{body['raw_token']}", headers=invitee["headers"])
    assert acc.status_code == 400

    db = SessionLocal()
    try:
        assert db.query(ProjectInvitation).filter_by(id=body["id"]).first().status == "expired"
        assert db.query(ProjectMember).filter_by(project_id=project_id, user_id=invitee["id"]).first() is None
    finally:
        db.close()

    assert _invite(client, owner, project_id, invitee["email"]).status_code == 201


def test_unregistered_email_can_be_invited(client, test_user_factory):
    owner = test_user_factory("unrown")
    project_id = _create_project(client, test_user_factory, owner)
    resp = _invite(client, owner, project_id, "not_registered_yet_pytest@example.com")
    assert resp.status_code == 201
    assert resp.json()["invitee_id"] is None


def test_db_unique_pending_constraint_and_accept_transaction_atomicity(client, test_user_factory):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from app.crud.project import generate_invitation_token_pair

    owner = test_user_factory("dbown")
    invitee = test_user_factory("dbinv")
    project_id = _create_project(client, test_user_factory, owner)

    # 1. Tạo 1 lời mời pending qua API
    first = _invite(client, owner, project_id, invitee["email"])
    assert first.status_code == 201
    inv_id = first.json()["id"]
    raw_token = first.json()["raw_token"]

    # 2. Thử chèn trực tiếp vào DB thêm 1 dòng pending trùng (project_id, email khác hoa/thường) -> DB chặn bằng uq_invitations_pending
    db = SessionLocal()
    try:
        _, token_hash_2 = generate_invitation_token_pair()
        dup_row = ProjectInvitation(
            project_id=project_id,
            inviter_id=owner["id"],
            invitee_email=invitee["email"].upper(),
            role="member",
            token=token_hash_2,
            status="pending",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
        )
        db.add(dup_row)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
    finally:
        db.close()

    # 3. Kiểm tra tính nguyên tử (transaction atomicity) khi chấp nhận lời mời:
    # Nếu user đã có mặt trong project_members (giả lập xung đột PK khi insert), lời mời không bị đổi sang 'accepted'
    db = SessionLocal()
    try:
        db.add(ProjectMember(project_id=project_id, user_id=invitee["id"], role="member"))
        db.commit()
    finally:
        db.close()

    conflict_resp = client.post(f"/api/invitations/accept/{raw_token}", headers=invitee["headers"])
    assert conflict_resp.status_code == 400

    db = SessionLocal()
    try:
        inv_after = db.query(ProjectInvitation).filter_by(id=inv_id).first()
        assert inv_after.status == "pending"
    finally:
        db.close()

