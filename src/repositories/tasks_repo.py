from abc import ABC, abstractmethod

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.models import TaskORM
from src.repositories.repository import SQLAlchemyRepository


class TaskWriter(ABC):
    @abstractmethod
    async def add_task(self, data: dict, creator_id: int):
        pass

    @abstractmethod
    async def delete_task_by_id(self, task_id: int):
        pass

    @abstractmethod
    async def assign_to_user(self, task_id: int, user_id: int):
        pass

    @abstractmethod
    async def update_task_by_id(self, task: TaskORM, data: dict):
        pass


class TaskReader(ABC):
    @abstractmethod
    async def get_by_user_id(
            self,
            user_id: int,
            limit: int | None = None,
            offset: int | None = None,
    ): pass

    @abstractmethod
    async def get_tasks_with_relations(
            self,
            limit: int | None = None,
            offset: int | None = None,
    ): pass

    @abstractmethod
    async def get_tasks_by_team_id(
            self,
            team_id: int,
            limit: int | None = None,
            offset: int | None = None,
    ): pass

    @abstractmethod
    async def get_task_by_id(self, task_id: int):
        pass

    @abstractmethod
    async def get_task_by_id_with_relations(self, task_id: int):
        pass



class TasksRepository(SQLAlchemyRepository, TaskWriter, TaskReader):
    model = TaskORM


    async def add_task(self, data: dict, creator_id: int):
        obj = self.model(**data, creator_id=creator_id)
        self.session.add(obj)
        await self.session.flush()

        return obj


    async def get_by_user_id(
        self,
        user_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ):
        stmt = (
            select(self.model)
            .where(self.model.executor_id == user_id)
            .order_by(self.model.id)
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.scalars(stmt)
        tasks = result.all()

        return tasks

    async def get_tasks_with_relations(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ):
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.comments),
                selectinload(self.model.executor),
                selectinload(self.model.team),
                selectinload(self.model.evaluation),
            )
            .order_by(self.model.id)
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.scalars(stmt)
        return result.all()


    async def update_task_by_id(self, task: TaskORM, data: dict):
        for field, value in data.items():
            setattr(task, field, value)

        await self.session.flush()
        await self.session.refresh(task)

        return task


    async def get_tasks_by_team_id(
        self,
        team_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ):
        stmt = (
            select(self.model)
            .where(self.model.team_id == team_id)
            .order_by(self.model.id)
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.scalars(stmt)
        tasks = result.all()

        return tasks


    async def get_task_by_id(self, task_id: int):
        stmt = select(self.model).where(self.model.id==task_id)
        task = await self.session.scalar(stmt)

        return task

    async def get_task_by_id_with_relations(self, task_id: int):
        stmt = (
            select(self.model)
            .where(self.model.id == task_id)
            .options(
                selectinload(self.model.comments),
                selectinload(self.model.executor),
                selectinload(self.model.team),
                selectinload(self.model.evaluation),
            )
        )
        return await self.session.scalar(stmt)


    async def delete_task_by_id(self, task_id: int):
        stmt = select(self.model).where(self.model.id == task_id)
        task = await self.session.scalar(stmt)

        await self.session.delete(task)
        await self.session.flush()

        return task


    async def assign_to_user(self, task_id: int, user_id: int):
        stmt = ((update(self.model)
                .where(self.model.id==task_id))
                .values(executor_id=user_id)
                .returning(self.model))
        result = await self.session.execute(stmt)

        return result.scalar()