from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


if TYPE_CHECKING:
    from src.models.tasks import TaskORM
    from src.models.meetings import MeetingORM
    from src.models.memberships import MembershipORM



class TeamORM(Base):
    """
    Модель команд
    """

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    memberships: Mapped[list["MembershipORM"]] = relationship(
        "MembershipORM", back_populates="team", cascade="all, delete-orphan"
    )

    tasks: Mapped[list["TaskORM"]] = relationship("TaskORM",
                                                  back_populates="team")

    meetings: Mapped[list["MeetingORM"]] = relationship(
        "MeetingORM", back_populates="team"
    )

    def __str__(self):
        return self.name
