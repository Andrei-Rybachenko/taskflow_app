from pydantic import ConfigDict, BaseModel


class UserShort(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class TeamShort(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class TaskShort(BaseModel):
    id: int
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class MeetingShort(BaseModel):
    id: int
    title: str
    team_id: int

    model_config = ConfigDict(from_attributes=True)


class MembershipShort(BaseModel):
    user_id: int
    team_id: int

    model_config = ConfigDict(from_attributes=True)


class CommentShort(BaseModel):
    id: int
    task_id: int
    author_id: int

    model_config = ConfigDict(from_attributes=True)
