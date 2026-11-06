from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.common import ID, TimestampMixin


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_task_created", "task_id", "created_at"),
        Index("ix_comments_parent_id", "parent_id"),
    )

    id = Column(ID, primary_key=True, autoincrement=True)
    task_id = Column(ID, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(ID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    parent_id = Column(ID, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    edited_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(ID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    task = relationship("Task")
    author = relationship("User", foreign_keys=[user_id])
    deleter = relationship("User", foreign_keys=[deleted_by])
    parent = relationship(
        "Comment",
        remote_side="Comment.id",
        back_populates="replies",
    )
    replies = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Comment.created_at",
    )

    @property
    def is_reply(self) -> bool:
        return self.parent_id is not None

    @property
    def is_edited(self) -> bool:
        return self.edited_at is not None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def edit(self, content: str) -> None:
        self.content = content
        self.edited_at = datetime.now()

    def soft_delete(self, deleted_by_id: int) -> None:
        self.deleted_at = datetime.now()
        self.deleted_by = deleted_by_id

    def __repr__(self) -> str:
        return f"<Comment id={self.id} task_id={self.task_id} parent_id={self.parent_id}>"
