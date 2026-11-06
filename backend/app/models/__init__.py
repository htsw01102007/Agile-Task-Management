# Import mọi model ở đây để Base.metadata.create_all() "nhìn thấy" và tạo bảng.
# Thêm model mới -> nhớ thêm 1 dòng import vào file này.
from app.models.activity_enums import ActivityAction, EntityType
from app.models.activity_log import ActivityLog
from app.models.checklist_item import ChecklistItem
from app.models.comment import Comment
from app.models.common import TimestampMixin
from app.models.entities import Project, Task, TaskList, User
from app.models.item import Item
from app.models.label import Label, TaskLabel
