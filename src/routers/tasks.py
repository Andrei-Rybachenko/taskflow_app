from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.auth.utils import current_active_user
from src.database import get_async_session
from src.dependencies import manager_required, admin_or_manager_required
from src.models import User, TeamORM
from src.schemas.common_schemas import TaskShort
from src.schemas.tasks import TaskCreate, TaskRead, TaskUpdate
from src.models.tasks import TaskORM


tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@tasks_router.get("",
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


@tasks_router.get("/my",
                  response_model=list[TaskRead],
                  status_code=status.HTTP_200_OK)
async def get_my_tasks(
        current_user: User = Depends(current_active_user),
        db: AsyncSession = Depends(get_async_session)):

    stmt = select(TaskORM).where(TaskORM.executor_id==current_user.id)

    result = await db.scalars(stmt)
    tasks = result.all()

    if not tasks:
        return []

    return tasks


@tasks_router.post("/{team_id}",
                   response_model=TaskShort,
                   status_code=status.HTTP_201_CREATED)


async def create_task(team_id: int,
                      task: TaskCreate,
                      current_user: User = Depends(admin_or_manager_required),
                      db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для создания задачи.

    """

    new_task = TaskORM(**task.model_dump(),
                       creator_id=current_user.id,
                       team_id=team_id)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@tasks_router.patch("/{task_id}",
                  response_model=TaskRead,
                  status_code=status.HTTP_200_OK)
async def update_task(
        team_id: int,
        task_id: int,
        task_update: TaskUpdate,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):
    """

    Ручка для изменения задачи.

    """

    stmt = select(TeamORM).where(TeamORM.id==team_id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не существует."
        )

    stmt = select(TaskORM).where(TaskORM.id==task_id)
    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не существует."
        )

    await db.execute(
        update(TaskORM)
        .where(TaskORM.id==task_id)
        .values(**task_update.model_dump(exclude_unset=True))
        )

    await db.commit()
    await db.refresh(task)

    return task


@tasks_router.get('/{team_id}',
                  response_model=list[TaskRead],
                  status_code=status.HTTP_200_OK)
async def get_tasks_by_team_id(
        team_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

        Ручка возвращает задачи команды по id.

    """

    stmt = select(TeamORM).where(TeamORM.id==team_id)
    team = await db.scalar(stmt)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой команды не существует"
        )

    stmt = select(TaskORM).where(TaskORM.team_id==team_id)
    result = await db.scalars(stmt)
    tasks = result.all()

    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="У данной команды пока нет задач"
        )

    return tasks


@tasks_router.get('/task_id}',
                  response_model=TaskRead,
                  status_code=status.HTTP_200_OK)
async def get_task_by_id(
        team_id: int,
        task_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

        Ручка возвращает задачу по id.

    """

    stmt = select(TaskORM).where(
        TaskORM.team_id==team_id,
        TaskORM.id==task_id
    )

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой задачи не существует"
        )

    return task


@tasks_router.delete('/{task_id}',
                  status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_id(
        team_id: int,
        task_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

    Ручка удаляет задачу по id.

    """

    stmt = select(TaskORM).where(
        TaskORM.team_id==team_id,
        TaskORM.id==task_id
    )
    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой задачи не существует"
        )

    await db.delete(task)
    await db.commit()

