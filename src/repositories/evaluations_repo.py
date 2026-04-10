from abc import ABC, abstractmethod

from sqlalchemy import select

from src.models.evaluations import EvaluationORM
from src.repositories.repository import SQLAlchemyRepository


class EvaluationReader(ABC):
    @abstractmethod
    async def get_evaluation_by_task_id(self, task_id: int): pass


class EvaluationWriter(ABC):
    @abstractmethod
    async def add(self, data: dict, task_id: int, reviewer_id: int): pass


class EvaluationsRepository(SQLAlchemyRepository, EvaluationReader, EvaluationWriter):
    model = EvaluationORM

    async def get_evaluation_by_task_id(self, task_id: int):
        stmt = select(self.model).where(self.model.task_id==task_id)
        score = await self.session.scalar(stmt)

        return score


    async def add(self, data: dict, task_id: int, reviewer_id: int):
        score = self.model(**data, task_id=task_id, reviewer_id=reviewer_id)
        self.session.add(score)
        await self.session.commit()
        await self.session.refresh(score)

        return score