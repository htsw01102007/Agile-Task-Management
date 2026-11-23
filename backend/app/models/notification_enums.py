from enum import Enum


class NotificationType(str, Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_DUE_SOON = "task_due_soon"
    TASK_OVERDUE = "task_overdue"
    COMMENT_ADDED = "comment_added"
    MENTIONED = "mentioned"
    PROJECT_INVITED = "project_invited"
    MEMBER_JOINED = "member_joined"
    TASK_COMPLETED = "task_completed"
