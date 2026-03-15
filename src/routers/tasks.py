from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.users import current_active_user
from src.database import get_async_session
from src.models import User
from src.schemas.tasks import TaskCreate, TaskRead
from src.models.tasks import TaskORM


tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@tasks_router.get("/",
                  response_model=list[TaskRead],
                  status_code=status.HTTP_200_OK)
async def get_all_tasks(db: AsyncSession = Depends(get_async_session)):

    """

    Ручка возвращает все задачи.

    """
    stmt = select(TaskORM).order_by(TaskORM.id)
    result = await db.scalars(stmt)
    tasks = result.all()

    return tasks