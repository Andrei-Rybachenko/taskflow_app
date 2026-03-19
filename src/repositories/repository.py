from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):

    @abstractmethod
    async def add_one(self):
        raise NotImplementedError

    @abstractmethod
    async def find_all(self):
        raise NotImplementedError


class SQLAlchemyRepository(ABC):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session


    async def add_one(self, data: dict):
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        return obj


    async def delete(self, instance_id: int):
        stmt = select(self.model).where(self.model.id==instance_id)
        result = await self.session.scalar(stmt)

        await self.session.delete(result)
        await self.session.commit()


    async def find_all(self):
        stmt = select(self.model)
        result = await self.session.scalars(stmt)

        return result.all()

    async def find_one(self, instance_id: int):
        stmt = select(self.model).where(self.model.id==instance_id)
        result = await self.session.scalar(stmt)

        return result

