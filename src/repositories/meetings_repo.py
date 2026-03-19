from sqlalchemy import select

from src.models import MeetingORM
from src.repositories.repository import SQLAlchemyRepository
from src.schemas import MeetingCreate


class MeetingsRepository(SQLAlchemyRepository):
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

    async def get_meetings_by_team_id(self, team_id: int):
        stmt = select(self.model).where(self.model.team_id==team_id)
        meetings = await self.session.scalars(stmt)

        return meetings

