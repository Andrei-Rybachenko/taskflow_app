from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import String, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


if TYPE_CHECKING:
    from src.models.tasks import TaskORM
    from src.models.users import User


class CommentORM(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    task: Mapped["TaskORM"] = relationship("TaskORM",
                                           back_populates="comments")
    author: Mapped["User"] = relationship("User")

    def __str__(self):
        return self.content
