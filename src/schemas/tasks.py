from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.schemas import CommentRead
from src.schemas.common_schemas import UserShort, TeamShort
from src.enums import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str
    deadline: datetime
    team_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    team_id: Optional[int] = None


class TaskRead(BaseModel):
    id: int
    title: str
    description: str
    executor_id: int | None
    team_id: int | None = None
    creator_id: int
    deadline: datetime
    status: TaskStatus

    executor: UserShort | None
    team: TeamShort | None
    comments: list[CommentRead] | None

    model_config = ConfigDict(from_attributes=True)
