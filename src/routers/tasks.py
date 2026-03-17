from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from src.routers import current_active_user
from src.database import get_async_session
from src.dependencies import admin_or_manager_required, admin_required
from src.models import User, TeamORM, MembershipORM
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
async def get_all_tasks(_: User = Depends(admin_required),
                        db: AsyncSession = Depends(get_async_session)):

    """

    Ручка возвращает все задачи.

    """
    stmt = select(TaskORM).order_by(TaskORM.id)
    result = await db.scalars(stmt)
    tasks = result.all()

    return tasks


@tasks_router.get("/my",
                  response_model=list[TaskShort],
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


@tasks_router.post("/{team_id}/create",
                   response_model=TaskRead,
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

    stmt = (
        select(TaskORM)
        .where(TaskORM.id == new_task.id)
        .options(
            selectinload(TaskORM.team),
            selectinload(TaskORM.comments),
            selectinload(TaskORM.executor)
        )
    )

    task = await db.scalar(stmt)

    return task


@tasks_router.patch("/{task_id}/update",
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


@tasks_router.get('/{team_id}/tasks',
                  response_model=list[TaskShort],
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


@tasks_router.get('/{task_id}',
                  response_model=TaskRead,
                  status_code=status.HTTP_200_OK)
async def get_task_by_id(
        task_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

    Ручка возвращает задачу по id.

    """

    stmt = (select(TaskORM)
            .where(TaskORM.id==task_id)
            .options(selectinload(TaskORM.comments),
                     selectinload(TaskORM.team),
                     selectinload(TaskORM.executor)))

    results = await db.execute(stmt)
    task = results.scalar()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой задачи не существует"
        )

    return task


@tasks_router.delete('/{task_id}/delete',
                  status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_id(
        task_id: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    """

    Ручка удаляет задачу по id.

    """

    stmt = select(TaskORM).where(TaskORM.id==task_id)
    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой задачи не существует"
        )

    await db.delete(task)
    await db.commit()


@tasks_router.patch("/{task_id}/assign",
                    response_model=TaskRead,
                    status_code=status.HTTP_200_OK)
async def assign_task_to_user(
        task_id: int,
        user_to_assign: int,
        _: User = Depends(admin_or_manager_required),
        db: AsyncSession = Depends(get_async_session)):

    stmt = (select(TaskORM)
            .where(TaskORM.id == task_id)
            .options(selectinload(TaskORM.comments),
                     selectinload(TaskORM.team),
                     selectinload(TaskORM.executor)))

    task = await db.scalar(stmt)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена."
        )

    if task.executor_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Задача уже назначена другому исполнителю."
        )

    stmt = (select(MembershipORM)
            .where(MembershipORM.user_id==user_to_assign,
                   MembershipORM.team_id==task.team_id))

    membership = await db.scalar(stmt)

    if not membership:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователю нельзя назначить эту задачу,"
                                   " так как он принадлежит другой команде.")

    task.executor_id = user_to_assign
    await db.commit()
    await db.refresh(task)

    return task