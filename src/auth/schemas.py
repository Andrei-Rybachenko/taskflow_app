from datetime import datetime
from fastapi_users import schemas
from pydantic import ConfigDict


class UserRead(schemas.BaseUser[int]):
    id: int
    username: str
    created_at: datetime

    # tasks: list[TaskShort] | None
    # meetings: list[MeetingShort] | None
    # memberships: list[MembershipShort] | None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    username: str


class UserUpdate(schemas.BaseUserUpdate):
    username: str
