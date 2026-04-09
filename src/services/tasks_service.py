from fastapi import HTTPException
from starlette import status

from src.repositories.membership_repo import MembershipsRepository, MembershipReader
from src.repositories.tasks_repo import TasksRepository, TaskReader, TaskWriter
from src.repositories.teams_repo import TeamsRepository, TeamReader
from src.schemas import TaskCreate, TaskUpdate


class TasksService:
    def __init__(
            self,
            task_reader: TaskReader,
            task_writer: TaskWriter,
            team_reader: TeamReader,
            membership_reader: MembershipReader


    ):
        self.task_writer = task_writer
        self.task_reader = task_reader
        self.team_reader = team_reader
        self.membership_reader = membership_reader


    async def create(self, task: TaskCreate, creator_id: int):
        new_task = task.model_dump()

        try:
            created = await self.task_writer.add_task(new_task, creator_id=creator_id)
            return await self.task_reader.get_task_by_id_with_relations(created.id)
        except Exception:
            raise


    async def delete(self, task_id: int):
        try:
            deleted_task = await self.task_writer.delete_task_by_id(task_id)
        except Exception:
            raise

        if not deleted_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой задачи не существует"
            )

        return deleted_task


    async def get_tasks(self, limit: int | None = None, offset: int | None = None):
        tasks = await self.task_reader.get_tasks_with_relations(limit=limit, offset=offset)
        return tasks


    async def get_task_or_404(self, task_id: int):
        task = await self.task_reader.get_task_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой задачи не существует"
            )

        return task

    async def get_task_with_relations_or_404(self, task_id: int):
        task = await self.task_reader.get_task_by_id_with_relations(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой задачи не существует"
            )

        return task


    async def get_users_tasks(self, current_user: int, limit: int | None = None, offset: int | None = None):
        tasks = await self.task_reader.get_by_user_id(current_user, limit=limit, offset=offset)
        return tasks


    async def update(self, task_update: TaskUpdate, task_id: int):
        task = await self.task_reader.get_task_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не существует."
            )

        try:
            updated_task = await self.task_writer.update_task_by_id(
                task,
                task_update.model_dump(exclude_unset=True)
            )

            return await self.task_reader.get_task_by_id_with_relations(updated_task.id)
        except Exception:
            raise


    async def get_team_tasks(self, team_id: int, limit: int | None = None, offset: int | None = None):
        team = await self.team_reader.get_team_with_relations(team_id)

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Такой команды не существует"
            )

        tasks = await self.task_reader.get_tasks_by_team_id(team_id, limit=limit, offset=offset)

        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="У данной команды пока нет задач",
            )

        return tasks

    async def assign(self, task_id, user_to_assign):
        task = await self.task_reader.get_task_by_id(task_id)

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

        membership = await self.membership_reader.get_membership(user_to_assign,
                                                                task.team_id)

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователю нельзя назначить эту задачу,"
                       " так как он принадлежит другой команде.",
            )

        try:
            await self.task_writer.assign_to_user(task_id, user_to_assign)
            return await self.task_reader.get_task_by_id_with_relations(task_id)
        except Exception:
            raise