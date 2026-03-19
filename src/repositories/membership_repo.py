from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from src.models import MembershipORM
from src.repositories.repository import SQLAlchemyRepository


class MembershipsRepository(SQLAlchemyRepository):
    model = MembershipORM


    async def get_membership(self, user_id: int, team_id: int):
        stmt = (select(self.model)
                      .where(self.model.user_id==user_id,
                             self.model.team_id==team_id)
                .options(joinedload(self.model.user)))

        membership = await self.session.scalar(stmt)

        return membership


    async def delete_member(self, user_id: int, team_id: int):
        stmt = (select(self.model)
                .where(self.model.user_id==user_id,
                       self.model.team_id==team_id))

        membership = await self.session.scalar(stmt)
        await self.session.delete(membership)
        await self.session.commit()

        return membership


    async def get_team_members(self, team_id: int):
        stmt = (
            select(self.model)
            .where(self.model.team_id == team_id)
            .options(joinedload(self.model.user))
        )

        members = await self.session.scalars(stmt)

        return members.all()


    async def update(
            self,
            data: dict,
            user_id: int,
            team_id: int
    ):
        stmt = (update(self.model)
                .where(self.model.user_id==user_id,
                       self.model.team_id==team_id)
                .values(**data)
                .returning(self.model))

        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.scalar()