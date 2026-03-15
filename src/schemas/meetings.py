from datetime import datetime
from pydantic import BaseModel, ConfigDict

from src.schemas.common_schemas import UserShort, TeamShort


class MeetingCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime


class MeetingUpdate(BaseModel):
    title: str | None
    team_id: int | None
    start_time: datetime | None
    end_time: datetime | None


class MeetingRead(BaseModel):
    id: int
    title: str
    team_id: int
    start_time: datetime
    end_time: datetime
    creator_id: int

    # team: TeamShort
    # users: list[UserShort]

    model_config = ConfigDict(from_attributes=True)