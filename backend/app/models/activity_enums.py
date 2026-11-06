from enum import Enum


class EntityType(str, Enum):
    PROJECT = "project"
    LIST = "list"
    TASK = "task"
    MEMBER = "member"
    INVITATION = "invitation"
    COMMENT = "comment"
    LABEL = "label"
    CHECKLIST_ITEM = "checklist_item"
    ATTACHMENT = "attachment"


class ActivityAction(str, Enum):
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"

    LIST_CREATED = "list.created"
    LIST_UPDATED = "list.updated"
    LIST_DELETED = "list.deleted"

    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    TASK_MOVED = "task.moved"
    TASK_PRIORITY_CHANGED = "task.priority_changed"
    TASK_DUE_DATE_CHANGED = "task.due_date_changed"
    TASK_ASSIGNEE_ADDED = "task.assignee_added"
    TASK_ASSIGNEE_REMOVED = "task.assignee_removed"

    MEMBER_ADDED = "member.added"
    MEMBER_REMOVED = "member.removed"

    INVITATION_SENT = "invitation.sent"

    COMMENT_CREATED = "comment.created"
    COMMENT_UPDATED = "comment.updated"
    COMMENT_DELETED = "comment.deleted"

    LABEL_CREATED = "label.created"
    LABEL_UPDATED = "label.updated"
    LABEL_DELETED = "label.deleted"
    LABEL_ATTACHED = "label.attached"
    LABEL_DETACHED = "label.detached"

    CHECKLIST_ITEM_CREATED = "checklist_item.created"
    CHECKLIST_ITEM_UPDATED = "checklist_item.updated"
    CHECKLIST_ITEM_DELETED = "checklist_item.deleted"
