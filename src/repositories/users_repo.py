from sqlalchemy import insert, select

from src.models import User
from src.repositories.repository import SQLAlchemyRepository


class UsersRepository(SQLAlchemyRepository):
    model = User

    async def get_user(self, user_id: int):
        stmt = select(self.model).where(self.model.id==user_id,
                                        self.model.is_active==True)

        user = await self.session.scalar(stmt)

        return user
