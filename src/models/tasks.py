from datetime import datetime

from sqlalchemy import Integer, String, Enum, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.enums import TaskStatus
from src.models.evaluations import EvaluationORM
from src.models.comments import CommentORM
from src.database import Base


class TaskORM(Base):
    """
    Таблица задач
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(String(200))
    executor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.OPEN)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

    executor: Mapped["User"] = relationship(
        "User",
        back_populates="tasks",
        foreign_keys=[executor_id])

    team: Mapped["TeamORM"] = relationship(
        "TeamORM",
        back_populates="tasks")

    evaluation: Mapped["EvaluationORM"] = relationship(
        "EvaluationORM",
        back_populates="task",
        uselist=False)

    comments: Mapped[list["CommentORM"]] = relationship(
        "CommentORM",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def __str__(self):
        return self.title or f"Task {self.id}"