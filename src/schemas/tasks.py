from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.common_schemas import UserShort, TeamShort, CommentShort
from src.enums import TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: str
    executor_id: int | None
    team_id: int
    deadline: datetime


class TaskUpdate(BaseModel):
    title: str | None
    description: str | None
    executor_id: int | None
    team_id: int | None
    deadline: datetime | None
    status: TaskStatus | None


class TaskRead(BaseModel):
    id: int
    title: str
    description: str
    executor_id: int | None
    team_id: int
    creator_id: int
    deadline: datetime
    status: TaskStatus

    # executor: UserShort | None
    # team: TeamShort
    # comments: list[CommentShort]

    model_config = ConfigDict(from_attributes=True)


