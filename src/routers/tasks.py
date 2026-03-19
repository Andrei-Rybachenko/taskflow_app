from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status
from src.routers import current_active_user
from src.dependencies import admin_or_manager_required, tasks_service
from src.models import User
from src.schemas.common_schemas import TaskShort
from src.schemas.tasks import TaskCreate, TaskRead, TaskUpdate
from src.services.tasks_service import TasksService

tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get(
    "",
    response_model=list[TaskRead],
    status_code=status.HTTP_200_OK)
async def get_all_tasks(
        service: Annotated[TasksService, Depends(tasks_service)]
):
    tasks = await service.get_tasks()
    return tasks


@tasks_router.get(
    "/my",
        response_model=list[TaskShort],
        status_code=status.HTTP_200_OK)
async def get_my_tasks(
    service: Annotated[TasksService, Depends(tasks_service)],
    current_user: User = Depends(current_active_user),
):
    my_tasks = await service.get_users_tasks(current_user.id)
    return my_tasks


@tasks_router.post(
    "/create",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED
)
async def create_task(
    task: TaskCreate,
    service: Annotated[TasksService, Depends(tasks_service)],
    current_user: User = Depends(admin_or_manager_required),
):
    """

    Ручка для создания задачи.

    """

    task = await service.create(task, current_user.id)
    return task


@tasks_router.patch(
    "/{task_id}/update",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK
)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    service: Annotated[TasksService, Depends(tasks_service)],
    _: User = Depends(admin_or_manager_required)
):
    """
    Ручка для изменения задачи.
    """

    updated_task = await service.update(task_update, task_id)

    return updated_task


@tasks_router.get(
    "/{team_id}/tasks",
    response_model=list[TaskShort],
    status_code=status.HTTP_200_OK
)
async def get_tasks_by_team_id(
    team_id: int,
    service: Annotated[TasksService, Depends(tasks_service)],
    _: User = Depends(admin_or_manager_required)
):
    """
    Ручка возвращает задачи команды по id.
    :param team_id:
    :param service:
    :param _:
    :return:
    """
    tasks = await service.get_team_tasks(team_id)

    return tasks


@tasks_router.get("/{task_id}",
                  response_model=TaskRead,
                  status_code=status.HTTP_200_OK)
async def get_task_by_id(
    task_id: int,
    service: Annotated[TasksService, Depends(tasks_service)],
    _: User = Depends(admin_or_manager_required)
):
    """
    Ручка возвращает задачу по id.
    """
    task = await service.get_task_or_404(task_id)

    return task


@tasks_router.delete(
    "/{task_id}/delete",
            status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_by_id(
    task_id: int,
    service: Annotated[TasksService, Depends(tasks_service)],
    _: User = Depends(admin_or_manager_required)
):
    """
    Ручка удаляет задачу по id.
    """

    await service.delete(task_id)


@tasks_router.patch(
    "/{task_id}/assign",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK
)
async def assign_task_to_user(
    task_id: int,
    user_to_assign: int,
    service: Annotated[TasksService, Depends(tasks_service)],
    _: User = Depends(admin_or_manager_required)
):

    task = await service.assign(task_id, user_to_assign)
    return task