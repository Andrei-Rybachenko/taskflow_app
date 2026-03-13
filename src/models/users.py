from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from src.dependencies import get_async_session
from src.models.meetings import meeting_participants
from src.models.tasks import TaskORM
from src.database import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tasks: Mapped[list["TaskORM"] | None] = relationship("TaskORM",
                                                  back_populates="executor",
                                                  foreign_keys=[TaskORM.executor_id]
                                                  )

    meetings: Mapped[list["MeetingORM"] | None] = relationship(
        "MeetingORM",
        secondary=meeting_participants,
        back_populates="users"
    )
    memberships: Mapped[list["MembershipORM"] | None] = relationship(
        "MembershipORM",
        back_populates="user"
    )

