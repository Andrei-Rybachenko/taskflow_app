from datetime import datetime

from sqlalchemy import Integer, ForeignKey, String, DateTime, func
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.database import Base


class EvaluationORM(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    comment: Mapped[str] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task: Mapped["TaskORM"] = relationship(
        "TaskORM",
        back_populates="evaluation",
        uselist=False
    )
    reviewer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reviewer_id]
    )
    employee: Mapped["User"] = relationship(
        "User",
        foreign_keys=[employee_id]
    )

    def __str__(self):
        return self.comment
