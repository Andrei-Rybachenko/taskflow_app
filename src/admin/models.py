from sqladmin import ModelView

from src.models.users import User
from src.models.tasks import TaskORM


class UserAdmin(ModelView, model=User):
    column_list = "__all__"


class TaskAdmin(ModelView, model=TaskORM):
    column_list = "__all__"

    name_plural = "Tasks"