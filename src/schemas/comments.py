from datetime import datetime

from pydantic import BaseModel, ConfigDict

class CommentCreate(BaseModel):
    task_id: int
    content: str


class CommentUpdate(BaseModel):
    content: str | None


class CommentRead(BaseModel):
    id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime

    # task: TaskShort
    # author: UserShort

    model_config = ConfigDict(from_attributes=True)
