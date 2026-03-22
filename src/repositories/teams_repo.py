from sqlalchemy import insert, select

from src.models import TeamORM, MembershipORM
from src.repositories.repository import SQLAlchemyRepository


class TeamsRepository(SQLAlchemyRepository):
    model = TeamORM


    async def add_team(self, data: dict, owner_id: int):
        obj = self.model(**data, owner_id=owner_id)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        return obj


    async def get_by_user_id(self, user_id: int):
        stmt = (select(self.model).join(self.model.memberships)
                .where(MembershipORM.user_id==user_id))

        result = await self.session.scalars(stmt)
        teams = result.all()

        return teams

