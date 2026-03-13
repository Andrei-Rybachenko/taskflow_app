from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.database import get_async_session
from src.schemas.tasks import TaskCreate, TaskRead
from src.models.tasks import TaskORM


tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@tasks_router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_async_session)):

    new_task = TaskORM(**task.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@tasks_router.get("/", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
async def get_all_tasks(db: AsyncSession = Depends(get_async_session)):

    stmt = select(TaskORM).order_by(TaskORM.id)
    result = await db.scalars(stmt)
    tasks = result.all()

    return tasks