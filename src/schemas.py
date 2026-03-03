from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.models import TaskStatus


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(min_length=8, description="Пароль (минимум 8 символов)")
    # role: str = Field(default="buyer", pattern="^(buyer|seller)$", description="Роль: 'buyer' или 'seller'")


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    # is_active: bool
    # role: str
    model_config = ConfigDict(from_attributes=True)


class Task(BaseModel):
    id: int
    name: str
    description: str
    executor: int
    deadline: date
    status: TaskStatus

    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    name: str
    description: str
    executor: int
    deadline: date
    status: TaskStatus
    created_at: datetime
