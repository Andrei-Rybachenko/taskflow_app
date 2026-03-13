from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.common_schemas import TaskShort, MembershipShort, MeetingShort


class TeamCreate(BaseModel):
    name: str


class TeamUpdate(BaseModel):
    name: str | None = None


class TeamRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    owner_id: int

    # memberships: list[MembershipShort]
    # tasks: list[TaskShort]
    # meetings: list[MeetingShort]

    model_config = ConfigDict(from_attributes=True)




