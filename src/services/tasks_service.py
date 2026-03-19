from fastapi import HTTPException
from starlette import status

from src.repositories.membership_repo import MembershipsRepository
from src.repositories.tasks_repo import TasksRepository
from src.repositories.teams_repo import TeamsRepository
from src.schemas import TaskCreate, TaskUpdate


class TasksService:
    def __init__(
            self,
            tasks_repo: TasksRepository,
            teams_repo: TeamsRepository,
            memberships_repo: MembershipsRepository

    ):
        self.tasks_repo = tasks_repo
        self.teams_repo = teams_repo
        self.memberships_repo = memberships_repo


    async def create(self, task: TaskCreate, creator_id: int):
        new_task = task.model_dump()
        task = await self.tasks_repo.add_task(new_task, creator_id=creator_id)
        return task


    async def delete(self, task_id: int):
        deleted_task = await self.tasks_repo.delete_task_by_id(task_id)

        if not deleted_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой задачи не существует"
            )

        return deleted_task


    async def get_tasks(self):
        tasks = await self.tasks_repo.find_all()
        return tasks


    async def get_task_or_404(self, task_id: int):
        task = await self.tasks_repo.get_task_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой задачи не существует"
            )

        return task


    async def get_users_tasks(self, current_user: int):
        tasks = await self.tasks_repo.get_by_user_id(current_user)
        return tasks


    async def update(self, task_update: TaskUpdate, task_id: int):
        # team = await self.teams_repo.get_by_team_id(team)
        #
        # if not team:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Команда не существует."
        #     )

        task = await self.tasks_repo.find_one(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не существует."
            )

        updated_task = await self.tasks_repo.update_task_by_id(
            task,
            task_update.model_dump(exclude_unset=True)
        )

        return updated_task


    async def get_team_tasks(self, team_id: int):
        team = await self.teams_repo.get_team_by_id(team_id)

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой команды не существует"
            )

        tasks = await self.tasks_repo.get_tasks_by_team_id(team_id)

        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="У данной команды пока нет задач",
            )

        return tasks

    async def assign(self, task_id, user_to_assign):
        task = await self.tasks_repo.get_task_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена."
            )

        if task.executor_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Задача уже назначена другому исполнителю.",
            )

        membership = await self.memberships_repo.get_membership(user_to_assign,
                                                                task.team_id)

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователю нельзя назначить эту задачу,"
                       " так как он принадлежит другой команде.",
            )

        task = await self.tasks_repo.assign_to_user(task_id, user_to_assign)

        return task