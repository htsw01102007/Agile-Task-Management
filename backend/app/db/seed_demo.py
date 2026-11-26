from __future__ import annotations

import json
import secrets
from datetime import date, datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_invitation import ProjectInvitation
from app.models.list import ListModel
from app.models.label import Label
from app.models.task import Task, TaskAssignee
from app.models.task_label import TaskLabel
from app.models.checklist import ChecklistItem
from app.models.comment import Comment
from app.models.attachment import Attachment
from app.models.notification import Notification
from app.models.activity_log import ActivityLog


DEMO_PASSWORD = "Password@123"


def _dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def ensure_demo_seed_data(db: Session) -> bool:
    """
    Tự động nạp bộ dữ liệu mẫu nhóm Agile Workspace nếu trong CSDL chưa có
    tài khoản nhóm trưởng 'binh.nd@agileworkspace.vn'.
    An toàn (idempotent): không xoá dữ liệu hiện có của người dùng.
    """
    existing_leader = (
        db.query(User)
        .filter(func.lower(User.email) == "binh.nd@agileworkspace.vn")
        .first()
    )
    if existing_leader is not None:
        return False

    pw_hash = hash_password(DEMO_PASSWORD)

    demo_users_spec = [
        ("admin", "admin@agileworkspace.vn", "nghiem_admin", "Quản Trị Hệ Thống", "admin", True),
        ("binh", "binh.nd@agileworkspace.vn", "nghiemdinhbinh", "Nghiêm Đình Bình", "user", True),
        ("quydung", "quydung.n@agileworkspace.vn", "nguyenquydung", "Nguyễn Quý Dũng", "user", True),
        ("minhson", "minhson.l@agileworkspace.vn", "leminhson", "Lê Minh Sơn", "user", True),
        ("ducminh", "ducminh.h@agileworkspace.vn", "haducminh", "Hà Đức Minh", "user", True),
        ("tandung", "tandung.n@agileworkspace.vn", "nguyentandung", "Nguyễn Tấn Dũng", "user", True),
        ("minhduong", "minhduong.nh@agileworkspace.vn", "minhduong", "Nguyễn Hữu Minh Dương", "user", True),
        ("locked", "locked.demo@agileworkspace.vn", "taikhoankhoa", "Tài Khoản Tạm Khóa", "user", False),
    ]

    users: dict[str, User] = {}
    for key, email, preferred_username, full_name, sys_role, is_active in demo_users_spec:
        target_username = "admin" if key == "admin" else preferred_username
        u = (
            db.query(User)
            .filter(
                (func.lower(User.email) == email.lower())
                | (func.lower(User.username) == target_username.lower())
            )
            .first()
        )
        if u:
            if key == "admin":
                u.email = email
                u.password_hash = pw_hash
                u.full_name = full_name
                u.system_role = "admin"
                u.is_active = True
            else:
                # Nếu trùng username với user cũ khác email thì tạo username riêng
                if u.email.lower() != email.lower():
                    u = User(
                        email=email,
                        username=f"{target_username}_aw",
                        password_hash=pw_hash,
                        full_name=full_name,
                        system_role=sys_role,
                        is_active=is_active,
                        token_version=0 if is_active else 1,
                    )
                    db.add(u)
                else:
                    u.password_hash = pw_hash
                    u.full_name = full_name
                    u.is_active = is_active
        else:
            u = User(
                email=email,
                username=target_username,
                password_hash=pw_hash,
                full_name=full_name,
                system_role=sys_role,
                is_active=is_active,
                token_version=0 if is_active else 1,
            )
            db.add(u)
        db.flush()
        users[key] = u

    # ── Tạo 4 Dự án mẫu đủ các trạng thái active / completed / archived ──
    p1 = Project(
        name="Phát triển Nền tảng Agile Workspace",
        description="Xây dựng hệ thống quản lý dự án & điều phối công việc nhóm theo thời gian thực với FastAPI, MySQL 8.0, WebSocket và giao diện Clean SaaS.",
        owner_id=users["binh"].id,
        status="active",
        start_date=date(2026, 9, 15),
        end_date=date(2026, 12, 20),
    )
    p2 = Project(
        name="Xây dựng Sàn Thương mại Điện tử Đa kênh",
        description="Phát triển hệ thống đặt hàng trực tuyến tích hợp giỏ hàng thông minh, cổng thanh toán VNPay, quản lý tồn kho và đối soát đơn hàng.",
        owner_id=users["quydung"].id,
        status="active",
        start_date=date(2026, 10, 1),
        end_date=date(2027, 1, 30),
    )
    p3 = Project(
        name="Chuẩn hóa Hệ thống Giao diện Clean SaaS v2",
        description="Thiết kế bộ quy chuẩn màu sắc Linear Indigo, hệ thống icon tối giản đồng nhất và hộp thoại tương tác cho toàn bộ 12 trang giao diện.",
        owner_id=users["minhson"].id,
        status="completed",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 10, 30),
    )
    p4 = Project(
        name="Nghiên cứu Khả thi Ứng dụng Quản lý Học tập",
        description="Dự án tiền khả thi giai đoạn trước đã được chuyển vào kho lưu trữ chỉ đọc để bảo toàn tài liệu tham khảo (dùng demo nút Khôi phục / Xoá).",
        owner_id=users["binh"].id,
        status="archived",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 31),
    )
    db.add_all([p1, p2, p3, p4])
    db.flush()

    # ── Thành viên dự án ──
    member_specs = [
        (p1.id, users["binh"].id, "owner"),
        (p1.id, users["quydung"].id, "manager"),
        (p1.id, users["minhson"].id, "member"),
        (p1.id, users["ducminh"].id, "member"),
        (p1.id, users["tandung"].id, "member"),
        (p1.id, users["minhduong"].id, "viewer"),
        (p2.id, users["quydung"].id, "owner"),
        (p2.id, users["binh"].id, "manager"),
        (p2.id, users["minhson"].id, "member"),
        (p2.id, users["ducminh"].id, "member"),
        (p3.id, users["minhson"].id, "owner"),
        (p3.id, users["binh"].id, "manager"),
        (p3.id, users["ducminh"].id, "member"),
        (p3.id, users["tandung"].id, "member"),
        (p4.id, users["binh"].id, "owner"),
        (p4.id, users["quydung"].id, "member"),
    ]
    for pid, uid, role in member_specs:
        db.add(ProjectMember(project_id=pid, user_id=uid, role=role))

    # ── Cột Kanban ──
    l1_todo = ListModel(project_id=p1.id, name="Cần làm", position=0, is_done_column=False)
    l1_doing = ListModel(project_id=p1.id, name="Đang triển khai", position=1, is_done_column=False)
    l1_qa = ListModel(project_id=p1.id, name="Đang kiểm thử (QA)", position=2, is_done_column=False)
    l1_done = ListModel(project_id=p1.id, name="Hoàn thành", position=3, is_done_column=True)

    l2_todo = ListModel(project_id=p2.id, name="Cần làm", position=0, is_done_column=False)
    l2_doing = ListModel(project_id=p2.id, name="Đang làm", position=1, is_done_column=False)
    l2_done = ListModel(project_id=p2.id, name="Hoàn thành", position=2, is_done_column=True)

    l3_todo = ListModel(project_id=p3.id, name="Cần làm", position=0, is_done_column=False)
    l3_doing = ListModel(project_id=p3.id, name="Đang làm", position=1, is_done_column=False)
    l3_done = ListModel(project_id=p3.id, name="Hoàn thành", position=2, is_done_column=True)

    l4_todo = ListModel(project_id=p4.id, name="Cần làm", position=0, is_done_column=False)
    l4_doing = ListModel(project_id=p4.id, name="Đang làm", position=1, is_done_column=False)
    l4_done = ListModel(project_id=p4.id, name="Hoàn thành", position=2, is_done_column=True)

    db.add_all([
        l1_todo, l1_doing, l1_qa, l1_done,
        l2_todo, l2_doing, l2_done,
        l3_todo, l3_doing, l3_done,
        l4_todo, l4_doing, l4_done,
    ])
    db.flush()

    # ── Nhãn màu ──
    lb_db = Label(project_id=p1.id, name="Database & ERD", color="#D97706")
    lb_api = Label(project_id=p1.id, name="Backend API", color="#2563EB")
    lb_fe = Label(project_id=p1.id, name="Frontend SaaS", color="#059669")
    lb_ws = Label(project_id=p1.id, name="Realtime WS", color="#7C3AED")
    lb_sec = Label(project_id=p1.id, name="Bảo mật & RBAC", color="#DC2626")
    lb_qa = Label(project_id=p1.id, name="Kiểm thử QA", color="#0EA5E9")
    lb_pay = Label(project_id=p2.id, name="Thanh toán", color="#F59E0B")
    lb_cart = Label(project_id=p2.id, name="Giỏ hàng", color="#4F46E5")
    lb_ui = Label(project_id=p3.id, name="UI/UX Minimal", color="#EC4899")
    db.add_all([lb_db, lb_api, lb_fe, lb_ws, lb_sec, lb_qa, lb_pay, lb_cart, lb_ui])
    db.flush()

    # ── Công việc Dự án 1 ──
    t1 = Task(
        project_id=p1.id, list_id=l1_done.id,
        title="Thiết kế sơ đồ ERD 16 bảng chuẩn hóa 3NF",
        description="Phân tích nghiệp vụ, thiết lập khóa ngoại kép (list_id, project_id) và cột ảo chống mời trùng.",
        priority="high", position=0,
        start_date=_dt("2026-09-16 08:00:00"), due_date=_dt("2026-09-28 17:00:00"),
        completed_at=_dt("2026-09-27 15:30:00"), created_by=users["binh"].id,
    )
    t2 = Task(
        project_id=p1.id, list_id=l1_done.id,
        title="Xây dựng xác thực JWT kép & Đăng nhập Google OAuth 2.0",
        description="Tích hợp Bcrypt 12 vòng, cơ chế Refresh Token tự động và liên kết tài khoản Google OpenID Connect.",
        priority="high", position=1,
        start_date=_dt("2026-09-28 08:00:00"), due_date=_dt("2026-10-12 17:00:00"),
        completed_at=_dt("2026-10-11 16:00:00"), created_by=users["minhson"].id,
    )
    t3 = Task(
        project_id=p1.id, list_id=l1_done.id,
        title="Phát triển bộ phân quyền dự án RBAC 4 cấp độ",
        description="Kiểm soát chặt quyền Owner, Manager, Member, Viewer ở cả tầng REST API lẫn kết nối WebSocket.",
        priority="high", position=2,
        start_date=_dt("2026-10-10 08:00:00"), due_date=_dt("2026-10-22 17:00:00"),
        completed_at=_dt("2026-10-21 14:20:00"), created_by=users["minhson"].id,
    )
    t4 = Task(
        project_id=p1.id, list_id=l1_done.id,
        title="Tái thiết kế giao diện Clean SaaS & Thanh tìm kiếm (/)",
        description="Đồng bộ logo tối giản, hộp thoại custom và thanh tìm kiếm điều hướng bằng phím mũi tên lên/xuống.",
        priority="medium", position=3,
        start_date=_dt("2026-10-22 08:00:00"), due_date=_dt("2026-11-08 17:00:00"),
        completed_at=_dt("2026-11-07 18:00:00"), created_by=users["binh"].id,
    )
    t5 = Task(
        project_id=p1.id, list_id=l1_done.id,
        title="Đồng bộ Realtime lời mời dự án & Kéo thả bảng Kanban",
        description="Đẩy thông báo tức thì qua /ws/notifications và đồng bộ di chuyển thẻ 0ms qua /ws/projects/{id}.",
        priority="urgent", position=4,
        start_date=_dt("2026-11-08 08:00:00"), due_date=_dt("2026-11-22 17:00:00"),
        completed_at=_dt("2026-11-21 20:15:00"), created_by=users["ducminh"].id,
    )
    t6 = Task(
        project_id=p1.id, list_id=l1_qa.id,
        title="Xây dựng Tab Thống kê tỷ lệ công việc từng thành viên",
        description="Tính toán tỷ lệ % khối lượng đảm nhận trong dự án và thanh tiến độ cá nhân cho từng thành viên.",
        priority="high", position=0,
        start_date=_dt("2026-11-20 08:00:00"), due_date=_dt("2026-12-08 17:00:00"),
        created_by=users["tandung"].id,
    )
    t7 = Task(
        project_id=p1.id, list_id=l1_qa.id,
        title="Viết bộ kiểm thử tự động Pytest & Đặc tả nghiệm thu (AC)",
        description="Kiểm thử luồng xác thực, chống mời trùng, kiểm tra Magic Bytes tệp tải lên và thu hồi quyền WebSocket.",
        priority="medium", position=1,
        start_date=_dt("2026-11-21 08:00:00"), due_date=_dt("2026-12-10 17:00:00"),
        created_by=users["tandung"].id,
    )
    t8 = Task(
        project_id=p1.id, list_id=l1_doing.id,
        title="Tối ưu truy vấn thống kê Dashboard & Nhật ký hoạt động",
        description="Giảm truy vấn lặp N+1 khi tải danh sách dự án và bổ sung phân trang cho bảng activity_logs.",
        priority="high", position=0,
        start_date=_dt("2026-11-18 08:00:00"), due_date=_dt("2026-12-12 17:00:00"),
        created_by=users["quydung"].id,
    )
    t9 = Task(
        project_id=p1.id, list_id=l1_doing.id,
        title="Hoàn thiện bộ Slide thuyết trình & Kịch bản Live Demo",
        description="Chuẩn bị sơ đồ ERD trực quan, phân công lời dẫn 10 phút cho 5 thành viên và kiểm tra đường truyền Vercel.",
        priority="urgent", position=1,
        start_date=_dt("2026-11-24 08:00:00"), due_date=_dt("2026-12-05 17:00:00"),
        created_by=users["binh"].id,
    )
    t10 = Task(
        project_id=p1.id, list_id=l1_todo.id,
        title="Tích hợp dịch vụ gửi Email SMTP tự động cho khách ngoài",
        description="Cấu hình hàng đợi gửi thư mời tự động qua SendGrid thay cho thao tác sao chép liên kết thủ công.",
        priority="medium", position=0,
        start_date=_dt("2026-11-05 08:00:00"), due_date=_dt("2026-11-20 17:00:00"),
        created_by=users["quydung"].id,
    )
    t11 = Task(
        project_id=p1.id, list_id=l1_todo.id,
        title="Nghiên cứu nâng cấp lưu trữ tệp đính kèm lên AWS S3",
        description="Đánh giá giải pháp Presigned URL để mở rộng dung lượng tệp tải lên trên môi trường đám mây.",
        priority="low", position=1,
        start_date=_dt("2026-12-01 08:00:00"), due_date=_dt("2026-12-18 17:00:00"),
        created_by=users["binh"].id,
    )
    t12 = Task(
        project_id=p1.id, list_id=l1_todo.id,
        title="Thử nghiệm giao diện tối tự động theo giờ hệ thống",
        description="Đầu việc thử nghiệm tạm đưa vào Thùng rác (có thể bấm nút Thùng rác trên bảng để khôi phục ngay).",
        priority="low", position=2,
        created_by=users["ducminh"].id,
        is_deleted=True, deleted_at=_dt("2026-11-23 16:00:00"),
    )

    # ── Công việc Dự án 2, 3, 4 ──
    t13 = Task(
        project_id=p2.id, list_id=l2_done.id,
        title="Thiết kế Schema Sản phẩm, Biến thể & Kho hàng",
        description="Chuẩn hóa bảng danh mục đa cấp, thuộc tính SKU và lịch sử xuất nhập tồn kho.",
        priority="high", position=0,
        completed_at=_dt("2026-10-17 15:00:00"), created_by=users["quydung"].id,
    )
    t14 = Task(
        project_id=p2.id, list_id=l2_doing.id,
        title="Tích hợp cổng thanh toán VNPay & Xác thực chữ ký IPN",
        description="Sinh URL thanh toán bảo mật HMAC-SHA512 và tự động cập nhật trạng thái đơn khi nhận Webhook.",
        priority="urgent", position=0,
        due_date=_dt("2026-12-15 17:00:00"), created_by=users["binh"].id,
    )
    t15 = Task(
        project_id=p2.id, list_id=l2_todo.id,
        title="Tối ưu bộ nhớ đệm danh sách sản phẩm bán chạy",
        description="Giảm thời gian phản hồi trang chủ dưới 100ms khi lượng truy cập tăng cao.",
        priority="medium", position=0,
        due_date=_dt("2026-12-25 17:00:00"), created_by=users["ducminh"].id,
    )
    t16 = Task(
        project_id=p3.id, list_id=l3_done.id,
        title="Thiết kế Logo hình học tối giản & Bộ màu Linear Indigo",
        priority="high", position=0,
        completed_at=_dt("2026-09-14 17:00:00"), created_by=users["minhson"].id,
    )
    t17 = Task(
        project_id=p3.id, list_id=l3_done.id,
        title="Xây dựng thư viện Icon Vector nét mảnh đồng bộ",
        priority="medium", position=1,
        completed_at=_dt("2026-10-04 16:00:00"), created_by=users["ducminh"].id,
    )
    t18 = Task(
        project_id=p4.id, list_id=l4_done.id,
        title="Khảo sát nhu cầu quản lý lịch ôn tập của sinh viên",
        priority="medium", position=0,
        completed_at=_dt("2026-07-19 16:00:00"), created_by=users["binh"].id,
    )

    db.add_all([t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16, t17, t18])
    db.flush()

    # ── Phân công người thực hiện ──
    assignees = [
        (t1.id, users["binh"].id), (t1.id, users["quydung"].id),
        (t2.id, users["minhson"].id),
        (t3.id, users["minhson"].id), (t3.id, users["quydung"].id),
        (t4.id, users["binh"].id), (t4.id, users["ducminh"].id),
        (t5.id, users["ducminh"].id), (t5.id, users["binh"].id),
        (t6.id, users["tandung"].id), (t6.id, users["ducminh"].id),
        (t7.id, users["tandung"].id),
        (t8.id, users["quydung"].id),
        (t9.id, users["binh"].id), (t9.id, users["minhson"].id), (t9.id, users["tandung"].id),
        (t10.id, users["quydung"].id),
        (t12.id, users["ducminh"].id),
        (t13.id, users["quydung"].id),
        (t14.id, users["binh"].id), (t14.id, users["minhson"].id),
        (t15.id, users["ducminh"].id),
        (t16.id, users["minhson"].id),
        (t17.id, users["ducminh"].id),
        (t18.id, users["binh"].id),
    ]
    for tid, uid in assignees:
        db.add(TaskAssignee(task_id=tid, user_id=uid))

    # ── Gắn nhãn ──
    task_label_pairs = [
        (t1.id, lb_db.id),
        (t2.id, lb_api.id), (t2.id, lb_sec.id),
        (t3.id, lb_api.id), (t3.id, lb_sec.id),
        (t4.id, lb_fe.id),
        (t5.id, lb_fe.id), (t5.id, lb_ws.id),
        (t6.id, lb_fe.id),
        (t7.id, lb_qa.id),
        (t8.id, lb_db.id), (t8.id, lb_api.id),
        (t9.id, lb_fe.id),
        (t10.id, lb_api.id),
        (t13.id, lb_cart.id), (t14.id, lb_pay.id),
        (t16.id, lb_ui.id), (t17.id, lb_ui.id),
    ]
    for tid, lid in task_label_pairs:
        db.add(TaskLabel(task_id=tid, label_id=lid))

    # ── Checklist mẫu ──
    checklists = [
        (t5.id, "Thiết lập WebSocket Connection Manager quản lý theo user_id và project_id", True, 0),
        (t5.id, "Đẩy sự kiện notification_created ngay khi tạo hoặc phản hồi lời mời", True, 1),
        (t5.id, "Đồng bộ thao tác kéo thả thẻ Kanban giữa nhiều cửa sổ trình duyệt", True, 2),
        (t5.id, "Bổ sung cơ chế Heartbeat ping/pong 20 giây và tự kết nối lại sau 3 giây", True, 3),
        (t6.id, "Tổng hợp thanh tiến độ Hoàn thành / Đang triển khai / Quá hạn toàn dự án", True, 0),
        (t6.id, "Tính tỷ lệ % khối lượng đảm nhận của từng thành viên trên tổng số việc", True, 1),
        (t6.id, "Tách nhóm công việc chưa phân công để trưởng nhóm dễ rà soát", True, 2),
        (t6.id, "Kiểm thử hiển thị tự động cập nhật khi kéo thả thẻ sang cột Hoàn thành", False, 3),
        (t9.id, "Hoàn thiện sơ đồ ERD 16 bảng đưa vào Slide thuyết trình Canva", True, 0),
        (t9.id, "Phân công thời lượng thuyết trình 10 phút cho 5 thành viên nhóm", True, 1),
        (t9.id, "Chạy thử kịch bản Live Demo 2 màn hình song song trước buổi bảo vệ", False, 2),
    ]
    for tid, content, done, pos in checklists:
        db.add(ChecklistItem(task_id=tid, content=content, is_done=done, position=pos))

    # ── Bình luận mẫu ──
    db.add_all([
        Comment(task_id=t5.id, user_id=users["ducminh"].id, content="Mình đã nối xong WebSocket ở cả layout.js và project.js, giờ gửi lời mời hoặc kéo thả task là bên kia nhảy ngay lập tức không cần F5."),
        Comment(task_id=t5.id, user_id=users["binh"].id, content="Quá mượt! Mình vừa mở thử 2 trình duyệt song song để test, thẻ nhảy không bị nháy khung hình chút nào."),
        Comment(task_id=t6.id, user_id=users["tandung"].id, content="Tab Thống kê công việc đã bổ sung đầy đủ phần trăm khối lượng dự án của từng thành viên, nhờ Bình và Quý Dũng xem qua nhé."),
        Comment(task_id=t9.id, user_id=users["minhson"].id, content="Phần bảo mật RBAC và tìm kiếm phím tắt (/) mình đã chuẩn bị sẵn ví dụ để phối hợp demo cùng cả nhóm."),
    ])

    # ── Lời mời đang chờ mẫu ──
    inv_pending = ProjectInvitation(
        project_id=p2.id,
        inviter_id=users["quydung"].id,
        invitee_email="tandung.n@agileworkspace.vn",
        invitee_id=users["tandung"].id,
        role="member",
        token=secrets.token_hex(32),
        status="pending",
        expires_at=_dt("2027-06-30 23:59:59"),
    )
    db.add(inv_pending)
    db.flush()

    # ── Thông báo mẫu ──
    db.add_all([
        Notification(
            user_id=users["binh"].id, type="comment_added",
            title="Hà Đức Minh đã bình luận trong công việc",
            message="Hà Đức Minh: Mình đã nối xong WebSocket ở cả layout.js và project.js...",
            entity_type="task", entity_id=t5.id, project_id=p1.id, is_read=False,
        ),
        Notification(
            user_id=users["binh"].id, type="comment_added",
            title="Nguyễn Tấn Dũng đã cập nhật tiến độ Thống kê",
            message="Tab Thống kê công việc đã bổ sung đầy đủ phần trăm khối lượng dự án của từng thành viên.",
            entity_type="task", entity_id=t6.id, project_id=p1.id, is_read=False,
        ),
        Notification(
            user_id=users["tandung"].id, type="invitation_sent",
            title=f"Lời mời tham gia dự án: {p2.name}",
            message=f"Nguyễn Quý Dũng mời bạn tham gia dự án '{p2.name}' với vai trò Member.",
            entity_type="invitation", entity_id=inv_pending.id, project_id=p2.id, is_read=False,
        ),
    ])

    # ── Nhật ký hoạt động mẫu ──
    db.add_all([
        ActivityLog(
            project_id=p1.id, user_id=users["binh"].id,
            entity_type="project", entity_id=p1.id, action="created",
            new_value=json.dumps({"name": p1.name}, ensure_ascii=False),
        ),
        ActivityLog(
            project_id=p1.id, task_id=t5.id, user_id=users["ducminh"].id,
            entity_type="task", entity_id=t5.id, action="moved",
            old_value=json.dumps({"column": "Đang kiểm thử (QA)"}, ensure_ascii=False),
            new_value=json.dumps({"column": "Hoàn thành"}, ensure_ascii=False),
        ),
        ActivityLog(
            project_id=p1.id, task_id=t9.id, user_id=users["binh"].id,
            entity_type="task", entity_id=t9.id, action="created",
            new_value=json.dumps({"title": t9.title, "priority": "urgent"}, ensure_ascii=False),
        ),
    ])

    db.commit()
    return True

