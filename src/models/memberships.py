from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.enums import Role


if TYPE_CHECKING:
    from src.models.teams import TeamORM
    from src.models.users import User


class MembershipORM(Base):
    __tablename__ = "memberships"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),
                                         primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"),
                                         primary_key=True)
    role: Mapped[Role] = mapped_column(
        Enum(Role), default=Role.EMPLOYEE, server_default="EMPLOYEE"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="memberships",
        lazy="selectin"
    )
    team: Mapped["TeamORM"] = relationship(
        "TeamORM",
        back_populates="memberships",
        lazy="selectin"
    )

    def __str__(self):
        return f"{self.role} Команда {self.team_id}"
