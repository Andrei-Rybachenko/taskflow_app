from abc import ABC, abstractmethod

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from src.models import TeamORM, MembershipORM, TaskORM, MeetingORM
from src.models.comments import CommentORM
from src.models.evaluations import EvaluationORM
from src.repositories.repository import SQLAlchemyRepository



class TeamReader(ABC):
    @abstractmethod
    async def get_by_user_id(
            self,
            user_id: int,
            limit: int | None = None,
            offset: int | None = None,
    ): pass

    @abstractmethod
    async def get_team_with_relations(self, team_id: int):
        pass


class TeamsRepository(SQLAlchemyRepository, TeamReader):
    model = TeamORM


    async def add_team(self, data: dict, owner_id: int):
        obj = self.model(**data, owner_id=owner_id)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        return obj


    async def get_by_user_id(
        self,
        user_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ):
        stmt = (
            select(self.model)
            .join(self.model.memberships)
            .where(MembershipORM.user_id == user_id)
            .order_by(self.model.id)
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.scalars(stmt)
        teams = result.all()

        return teams

    async def get_team_with_relations(self, team_id: int):

        stmt = (
            select(self.model)
            .where(self.model.id == team_id)
            .options(
                selectinload(self.model.memberships),
                selectinload(self.model.tasks),
                selectinload(self.model.meetings),
            )
        )
        return await self.session.scalar(stmt)

    async def delete_team_cascade(self, team_id: int) -> None:
        task_ids = (
            await self.session.scalars(
                select(TaskORM.id).where(TaskORM.team_id == team_id)
            )
        ).all()

        for tid in task_ids:
            await self.session.execute(
                delete(CommentORM).where(CommentORM.task_id == tid)
            )
            await self.session.execute(
                delete(EvaluationORM).where(EvaluationORM.task_id == tid)
            )

        await self.session.execute(delete(TaskORM).where(TaskORM.team_id == team_id))
        await self.session.execute(delete(MeetingORM).where(MeetingORM.team_id == team_id))
        await self.session.execute(
            delete(MembershipORM).where(MembershipORM.team_id == team_id)
        )
        await self.session.execute(delete(TeamORM).where(TeamORM.id == team_id))
        await self.session.commit()

