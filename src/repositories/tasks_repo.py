from sqlalchemy import insert, select, update

from src.models import TaskORM
from src.repositories.repository import SQLAlchemyRepository


class TasksRepository(SQLAlchemyRepository):
    model = TaskORM


    async def add_task(self, data: dict, creator_id: int):
        obj = self.model(**data, creator_id=creator_id)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        return obj


    async def get_by_user_id(self, user_id: int):
        stmt = select(self.model
                        ).where(self.model.executor_id==user_id)

        result = await self.session.scalars(stmt)
        tasks = result.all()

        return tasks


    async def update_task_by_id(self, task: TaskORM, data: dict):
        for field, value in data.items():
            setattr(task, field, value)

        await self.session.commit()
        await self.session.refresh(task)

        return task


    async def get_tasks_by_team_id(self, team_id: int):
        stmt = select(self.model).where(self.model.team_id == team_id)
        result = await self.session.scalars(stmt)
        tasks = result.all()

        return tasks


    async def get_task_by_id(self, task_id: int):
        stmt = select(self.model).where(self.model.id==task_id)
        task = await self.session.scalar(stmt)

        return task


    async def delete_task_by_id(self, task_id: int):
        stmt = select(self.model).where(self.model.id == task_id)
        task = await self.session.scalar(stmt)

        await self.session.delete(task)
        await self.session.commit()

        return task


    async def assign_to_user(self, task_id: int, user_id: int):
        stmt = ((update(self.model)
                .where(self.model.id==task_id))
                .values(executor_id=user_id)
                .returning(self.model))
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.scalar()