from sqlalchemy import insert, select

from src.models import TeamORM, MembershipORM
from src.repositories.repository import SQLAlchemyRepository


class TeamsRepository(SQLAlchemyRepository):
    model = TeamORM


    async def add_team(self, data: dict, owner_id: int):

        stmt = insert(self.model).values(
             **data,
            owner_id=owner_id
        ).returning(self.model)

        result = await self.session.execute(stmt)
        team = result.scalar()

        return team


    async def get_by_user_id(self, user_id: int):
        stmt = (select(self.model).join(self.model.memberships)
                .where(MembershipORM.user_id==user_id))

        result = await self.session.scalars(stmt)
        teams = result.all()

        return teams

