from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class EvaluationCreate(BaseModel):
    score: Annotated[int, Field(ge=1, le=5)]
    comment: str | None


class EvaluationUpdate(BaseModel):
    task_id: int | None
    reviewer_id: int | None
    employee_id: int | None
    score: Annotated[int, Field(ge=1, le=5)] | None
    comment: str | None


class EvaluationRead(BaseModel):
    id: int
    task_id: int
    reviewer_id: int
    employee_id: int
    score: Annotated[int, Field(ge=1, le=5)]
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
