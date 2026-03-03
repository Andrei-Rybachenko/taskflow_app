import enum
from datetime import datetime, date

from sqlalchemy import Integer, String, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class TaskStatus(enum.Enum):
    OPEN = "открыто"
    IN_PROGRESS = "в работе"
    FINISHED = "выполнено"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    executor: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    deadline: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
