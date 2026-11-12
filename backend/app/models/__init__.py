# Import mọi model ở đây để Base.metadata.create_all() "nhìn thấy" và tạo bảng.
# Thêm model mới -> nhớ thêm 1 dòng import vào file này.
from app.models.item import Item  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.project_member import ProjectMember  # noqa: F401
from app.models.list import ListModel  # noqa: F401
from app.models.task import Task, TaskAssignee, TaskLabel  # noqa: F401
from app.models.label import Label  # noqa: F401
from app.models.checklist import ChecklistItem  # noqa: F401
from app.models.comment import Comment, Attachment, ActivityLog  # noqa: F401
