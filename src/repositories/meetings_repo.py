from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models import MeetingORM
from src.repositories.repository import SQLAlchemyRepository
from src.schemas import MeetingCreate


class MeetingReader(ABC):
    @abstractmethod
    async def overlapping_meeting(self, new_meeting: MeetingCreate): pass

    @abstractmethod
    async def get_meetings_by_team_id(
            self,
            team_id: int,
            limit: int | None = None,
            offset: int | None = None,
    ): pass

    @abstractmethod
    async def get_meeting_with_relations(self, meeting_id: int): pass


class MeetingWriter(ABC):
    @abstractmethod
    async def add_meeting(self, data: dict, creator_id: int): pass

    @abstractmethod
    async def delete(self, instance_id: int): pass


class MeetingsRepository(SQLAlchemyRepository, MeetingReader, MeetingWriter):
    model = MeetingORM


    async def add_meeting(self, data: dict, creator_id: int):
        obj = self.model(**data, creator_id=creator_id)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)

        return obj


    async def overlapping_meeting(self, new_meeting: MeetingCreate):
        stmt = select(self.model).where(
            self.model.team_id == new_meeting.team_id,
            self.model.start_time < new_meeting.end_time,
            self.model.end_time > new_meeting.start_time,
        )

        result = await self.session.scalar(stmt)

        return result

    async def get_meetings_by_team_id(
        self,
        team_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ):
        stmt = (
            select(self.model)
            .where(self.model.team_id == team_id)
            .order_by(self.model.id)
            .options(
                selectinload(self.model.team),
                selectinload(self.model.users),
            )
        )
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        meetings = await self.session.scalars(stmt)

        return meetings.all()

    async def get_meeting_with_relations(self, meeting_id: int):
        stmt = (
            select(self.model)
            .where(self.model.id == meeting_id)
            .options(
                selectinload(self.model.team),
                selectinload(self.model.users),
            )
        )
        return await self.session.scalar(stmt)

