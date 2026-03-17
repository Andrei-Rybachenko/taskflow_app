from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.common_schemas import UserShort
from src.enums import Role


class MembershipCreate(BaseModel):
    user_id: int
    # team_id: int
    role: Role


class MembershipUpdate(BaseModel):
    role: Role | None


class MembershipRead(BaseModel):
    user_id: int
    team_id: int
    role: Role
    joined_at: datetime

    user: UserShort
    # team: TeamShort

    model_config = ConfigDict(from_attributes=True)
