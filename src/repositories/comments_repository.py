from sqlalchemy import select

from src.models.comments import CommentORM
from src.repositories.repository import SQLAlchemyRepository


class CommentsRepository(SQLAlchemyRepository):
    model = CommentORM


    async def add(self, data: dict, author_id: int):
        obj = self.model(**data, author_id=author_id)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        return obj


    async def delete(self, comment_id: int):
        stmt = select(self.model).where(self.model.id==comment_id)
        comment = await self.session.scalar(stmt)
        await self.session.delete(comment)
        await self.session.commit()


    async def get(self, task_id):
        stmt = select(self.model).where(self.model.task_id==task_id)
        results = await self.session.scalars(stmt)

        return results.all()
