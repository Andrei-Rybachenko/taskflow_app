from datetime import datetime

from sqlalchemy import Integer, ForeignKey, String, DateTime, func, Table, Column
from sqlalchemy.orm import mapped_column, Mapped, relationship

# from src.teams.models import TeamORM
from src.database import Base


meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column("meeting_id", Integer, ForeignKey("meetings.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)

class MeetingORM(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    title: Mapped[str] = mapped_column(String(100))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    team: Mapped["TeamORM"] = relationship(
        "TeamORM",
        back_populates="meetings"
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=meeting_participants,
        back_populates="meetings"
    )



